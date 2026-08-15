import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Electronic Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()
    
    date_col = [col for col in df.columns if 'date' in col.lower()]
    if date_col:
        df[date_col[0]] = pd.to_datetime(df[date_col[0]], errors='coerce')
        df['YearMonth'] = df[date_col[0]].dt.to_period('M').astype(str)
        df['Month'] = df[date_col[0]].dt.month
        df['DayOfWeek'] = df[date_col[0]].dt.day_name()
    
    cols_lower = {col.lower(): col for col in df.columns}
    if 'total price' not in cols_lower and 'total_amount' not in cols_lower:
        price_col = [c for c in df.columns if 'price' in c.lower()]
        qty_col = [c for c in df.columns if 'quantity' in c.lower() or 'qty' in c.lower()]
        if price_col and qty_col:
            df['Total Sales'] = df[price_col[0]] * df[qty_col[0]]
    else:
        sales_col = cols_lower.get('total price') or cols_lower.get('total_amount')
        df['Total Sales'] = df[sales_col]
        
    df = df.dropna(subset=['Total Sales'])
    return df

# 지정하신 데이터 파일명 적용
DATA_PATH = "Electronic_sales_Sep2023-Sep2024.csv" 

try:
    df = load_and_preprocess_data(DATA_PATH)
except Exception as e:
    st.error(f"데이터 파일('{DATA_PATH}')을 로드하는 중 오류가 발생했습니다. 저장소에 파일이 존재하는지 확인해 주세요.")
    st.stop()

# ---------------------------------------------------------
# [사이드바] 날짜 필터링
# ---------------------------------------------------------
st.sidebar.header("🔍 데이터 필터")

date_cols = [col for col in df.columns if 'date' in col.lower()]
date_col_name = date_cols[0] if date_cols else None

if date_col_name and pd.api.types.is_datetime64_any_dtype(df[date_col_name]):
    min_date = df[date_col_name].min().date()
    max_date = df[date_col_name].max().date()

    selected_date_range = st.sidebar.date_input(
        "📅 조회 기간 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = df[
            (df[date_col_name].dt.date >= start_date) & 
            (df[date_col_name].dt.date <= end_date)
        ]
    else:
        filtered_df = df.copy()
        start_date, end_date = min_date, max_date
else:
    filtered_df = df.copy()
    start_date, end_date = None, None

# ---------------------------------------------------------
# 3. 대시보드 헤더 및 주요 지표 (KPI)
# ---------------------------------------------------------
st.title("⚡ Electronic Sales Data Dashboard")
st.markdown("전자기기 판매 데이터 전처리 및 핵심 시각화 대시보드")

if start_date and end_date:
    st.caption(f"📅 **현재 집계 기간:** {start_date} ~ {end_date}")
else:
    st.caption("📅 **현재 집계 기간:** 전체 기간")

st.markdown("---")

# 고객 ID 컬럼 탐색
user_cols = [c for c in filtered_df.columns if 'customer' in c.lower() or 'user' in c.lower() or 'client' in c.lower()]
cust_col = user_cols[0] if user_cols else None

# === KPI 주요 지표 계산 ===
total_revenue = filtered_df['Total Sales'].sum()
total_orders = len(filtered_df)
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

if cust_col and cust_col in filtered_df.columns:
    total_customers = filtered_df[cust_col].nunique()
    arpu = total_revenue / total_customers if total_customers > 0 else 0  # 인당 객단가
    
    # 재구매율 계산 (2회 이상 구매 고객 비율)
    order_counts_per_cust = filtered_df.groupby(cust_col).size()
    repeat_customers = (order_counts_per_cust >= 2).sum()
    repeat_rate = (repeat_customers / total_customers * 100) if total_customers > 0 else 0
else:
    total_customers = 0
    arpu = 0
    repeat_rate = 0

# === KPI Row 1: 기본 실적 지표 ===
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
kpi_col1.metric("총 매출액 (Total Revenue)", f"${total_revenue:,.2f}")
kpi_col2.metric("총 주문 건수 (Total Orders)", f"{total_orders:,} 건")
kpi_col3.metric("평균 주문 금액 (건당)", f"${avg_order_value:,.2f}")

st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True) # 줄간격 여백

# === KPI Row 2: 고객 관점 지표 ===
kpi_col4, kpi_col5, kpi_col6 = st.columns(3)
if cust_col:
    kpi_col4.metric("총 주문 고객수 (Total Customers)", f"{total_customers:,} 명")
    kpi_col5.metric("인당 객단가 (Revenue / Customer)", f"${arpu:,.2f}")
    kpi_col6.metric("재구매율 (Repeat Purchase Rate)", f"{repeat_rate:.1f}%")
else:
    kpi_col4.metric("총 주문 고객수", "N/A")
    kpi_col5.metric("인당 객단가", "N/A")
    kpi_col6.metric("재구매율", "N/A")

st.markdown("---")

# ---------------------------------------------------------
# 4. 시각화 차트 구성 (메인 배치)
# ---------------------------------------------------------

col_left, col_right = st.columns([1.2, 0.8])

# === [좌측 컬럼] 통합 월별 매출 및 구매자 추이 ===
with col_left:
    st.subheader("📈 월별 매출 및 구매자 추이 (통합)")
    
    user_cols = [c for c in filtered_df.columns if 'customer' in c.lower() or 'user' in c.lower() or 'client' in c.lower()]
    
    if 'YearMonth' in filtered_df.columns and user_cols:
        cust_col = user_cols[0]
        
        # 월별 매출 및 구매자 수 데이터 집계
        monthly_df = filtered_df.groupby('YearMonth').agg(
            Sales=('Total Sales', 'sum'),
            Active_Users=(cust_col, 'nunique')
        ).reset_index()

        # 이중 축(Secondary Y-axis) 그래프 생성
        fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

        # 1) 매출액 (좌측 Y축 - 막대 그래프)
        fig_combined.add_trace(
            go.Bar(
                x=monthly_df['YearMonth'],
                y=monthly_df['Sales'],
                name="매출액 ($)",
                marker_color='#636EFA',
                opacity=0.75
            ),
            secondary_y=False
        )

        # 2) 구매자 수 (우측 Y축 - 꺾은선 그래프)
        fig_combined.add_trace(
            go.Scatter(
                x=monthly_df['YearMonth'],
                y=monthly_df['Active_Users'],
                name="구매자 수 (명)",
                mode="lines+markers",
                line=dict(color='#EF553B', width=3),
                marker=dict(size=7)
            ),
            secondary_y=True
        )

        # 축 레이블 및 레이아웃 설정
        fig_combined.update_layout(
            title_text="Monthly Revenue & Active Customers Trend",
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        fig_combined.update_yaxes(title_text="<b>매출액 ($)</b>", secondary_y=False)
        fig_combined.update_yaxes(title_text="<b>구매자 수 (명)</b>", secondary_y=True)

        st.plotly_chart(fig_combined, use_container_width=True)

        # --- 인사이트 섹션 ---
        if not monthly_df.empty:
            max_sales_row = monthly_df.loc[monthly_df['Sales'].idxmax()]
            max_users_row = monthly_df.loc[monthly_df['Active_Users'].idxmax()]
            
            st.info(
                f"💡 **월별 추이 인사이트**\n"
                f"- **최고 매출 달성 월:** {max_sales_row['YearMonth']} (${max_sales_row['Sales']:,.2f})\n"
                f"- **최다 구매자 방문 월:** {max_users_row['YearMonth']} ({max_users_row['Active_Users']:,} 명)\n"
                f"- 구매자 수 추이와 매출 곡선의 동행 여부를 통해 인당 객단가 변화 추이를 확인할 수 있습니다."
            )
    else:
        st.info("날짜 또는 고객 ID 컬럼을 찾을 수 없습니다.")

# === [우측 컬럼] Loyalty Member 구분별 지표 ===
with col_right:
    st.subheader("👑 Loyalty Member 구분별 지표")
    
    loyalty_cols = [c for c in filtered_df.columns if 'loyalty' in c.lower() or 'member' in c.lower()]
    
    if loyalty_cols:
        loyalty_col = loyalty_cols[0]
        loyalty_summary = filtered_df.groupby(loyalty_col).agg(
            Total_Sales=('Total Sales', 'sum'),
            Order_Count=('Total Sales', 'count')
        ).reset_index()

        fig_loyalty = px.pie(
            loyalty_summary,
            names=loyalty_col,
            values='Total_Sales',
            hole=0.4,
            title=f"Sales Share by {loyalty_col}",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_loyalty, use_container_width=True)

        # --- 인사이트 섹션 ---
        if not loyalty_summary.empty:
            loyalty_summary['Sales_Share'] = (loyalty_summary['Total_Sales'] / loyalty_summary['Total_Sales'].sum()) * 100
            top_member = loyalty_summary.loc[loyalty_summary['Total_Sales'].idxmax()]
            
            st.info(
                f"💡 **Loyalty 인사이트**\n"
                f"- **최대 매출 기여 그룹:** '{top_member[loyalty_col]}' ({top_member['Sales_Share']:.1f}% 점유)\n"
                f"- 로열티 회원과 비회원의 매출 비중 구조를 파악하여 회원제 리텐션 프로모션 전략 수립에 활용할 수 있습니다."
            )
    else:
        st.info("Loyalty Member 관련 컬럼을 찾을 수 없습니다.")

st.markdown("---")

# === 하단 영역: 카테고리 Top 10 및 결제 수단 ===
sub_col1, sub_col2 = st.columns(2)

with sub_col1:
    st.subheader("📦 카테고리/제품별 매출 Top 10")
    cat_cols = [c for c in filtered_df.columns if 'category' in c.lower() or 'product' in c.lower()]
    if cat_cols:
        target_cat = cat_cols[0]
        cat_sales = filtered_df.groupby(target_cat)['Total Sales'].sum().reset_index().sort_values(by='Total Sales', ascending=False).head(10)
        fig_bar = px.bar(cat_sales, x='Total Sales', y=target_cat, orientation='h', color='Total Sales', color_continuous_scale='Viridis')
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)

with sub_col2:
    st.subheader("💳 결제 수단 비중")
    pay_cols = [c for c in filtered_df.columns if 'payment' in c.lower() or 'type' in c.lower()]
    if pay_cols:
        pay_df = filtered_df[pay_cols[0]].value_counts().reset_index()
        pay_df.columns = [pay_cols[0], 'Count']
        fig_pie = px.pie(pay_df, names=pay_cols[0], values='Count', hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)