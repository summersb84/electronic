import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Electronic Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_preprocess_data(file_path):
    df = pd.read_csv("Electronic_sales_Sep2023-Sep2024.csv")
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

# 데이터 불러오기
DATA_PATH = "Electronic_sales_Sep2023-Sep2024.csv" 

try:
    df = load_and_preprocess_data(DATA_PATH)
except Exception as e:
    st.error(f"데이터 파일('{DATA_PATH}')을 로드하는 중 오류가 발생했습니다. 저장소에 파일이 존재하는지 확인해 주세요.")
    st.stop()

# ---------------------------------------------------------
# [사이드바] 날짜 필터링 로직
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

total_revenue = filtered_df['Total Sales'].sum()
total_orders = len(filtered_df)
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("총 매출액 (Total Revenue)", f"${total_revenue:,.2f}")
col2.metric("총 주문 건수 (Total Orders)", f"{total_orders:,} 건")
col3.metric("평균 주문 금액 (AOV)", f"${avg_order_value:,.2f}")

st.markdown("---")

# ---------------------------------------------------------
# 4. 시각화 차트 구성 (레이아웃 재배치)
# ---------------------------------------------------------

# === ROW 1: 월별 매출 추이 | 월별 구매자 추이 ===
row1_col1, row1_col2 = st.columns(2)

with row1_col1:
    st.subheader("📈 Chart 1: 월별 매출 추이")
    if 'YearMonth' in filtered_df.columns:
        monthly_sales = filtered_df.groupby('YearMonth')['Total Sales'].sum().reset_index()
        fig_sales = px.line(
            monthly_sales, 
            x='YearMonth', 
            y='Total Sales',
            markers=True,
            title="Monthly Sales Trend",
            labels={'YearMonth': '연월', 'Total Sales': '매출액 ($)'}
        )
        st.plotly_chart(fig_sales, use_container_width=True)
    else:
        st.info("날짜 컬럼을 찾을 수 없습니다.")

with row1_col2:
    st.subheader("👥 월별 구매자 추이")
    user_cols = [c for c in filtered_df.columns if 'customer' in c.lower() or 'user' in c.lower() or 'client' in c.lower()]
    
    if 'YearMonth' in filtered_df.columns and user_cols:
        cust_col = user_cols[0]
        monthly_users = filtered_df.groupby('YearMonth')[cust_col].nunique().reset_index()
        monthly_users.columns = ['YearMonth', 'Active Users']
        
        fig_users = px.bar(
            monthly_users,
            x='YearMonth',
            y='Active Users',
            title="Monthly Unique Customers",
            labels={'YearMonth': '연월', 'Active Users': '구매자 수 (명)'},
            color_discrete_sequence=['#636EFA']
        )
        st.plotly_chart(fig_users, use_container_width=True)
    else:
        st.info("고객 ID 또는 날짜 컬럼을 찾을 수 없어 구매자 추이를 표시하지 못했습니다.")


# === ROW 2: 카테고리/제품별 매출 Top 10 | Loyalty Member 구분별 지표 ===
row2_col1, row2_col2 = st.columns(2)

with row2_col1:
    st.subheader("📦 Chart 2: 카테고리/제품별 매출 Top 10")
    cat_cols = [c for c in filtered_df.columns if 'category' in c.lower() or 'product' in c.lower()]
    
    if cat_cols:
        target_cat = cat_cols[0]
        cat_sales = filtered_df.groupby(target_cat)['Total Sales'].sum().reset_index()
        cat_sales = cat_sales.sort_values(by='Total Sales', ascending=False).head(10)
        
        fig_bar = px.bar(
            cat_sales, 
            x='Total Sales', 
            y=target_cat, 
            orientation='h',
            color='Total Sales',
            color_continuous_scale='Viridis',
            title=f"Top Sales by {target_cat}",
            labels={'Total Sales': '매출액 ($)', target_cat: '카테고리/제품'}
        )
        fig_bar.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("카테고리 또는 제품 컬럼을 찾을 수 없습니다.")

with row2_col2:
    st.subheader("👑 Loyalty Member 구분별 지표")
    loyalty_cols = [c for c in filtered_df.columns if 'loyalty' in c.lower() or 'member' in c.lower()]
    
    if loyalty_cols:
        loyalty_col = loyalty_cols[0]
        loyalty_sales = filtered_df.groupby(loyalty_col)['Total Sales'].sum().reset_index()
        
        fig_loyalty = px.pie(
            loyalty_sales,
            names=loyalty_col,
            values='Total Sales',
            hole=0.4,
            title=f"Sales Share by {loyalty_col}",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig_loyalty, use_container_width=True)
    else:
        st.info("Loyalty Member 컬럼을 찾을 수 없습니다.")


# === ROW 3: 결제 수단 비중 | 데이터 미리보기 ===
row3_col1, row3_col2 = st.columns(2)

with row3_col1:
    st.subheader("💳 결제 수단 비중")
    pay_cols = [c for c in filtered_df.columns if 'payment' in c.lower() or 'type' in c.lower()]
    
    if pay_cols:
        pay_df = filtered_df[pay_cols[0]].value_counts().reset_index()
        pay_df.columns = [pay_cols[0], 'Count']
        
        fig_pie = px.pie(
            pay_df, 
            names=pay_cols[0], 
            values='Count',
            hole=0.4,
            title="Payment Method Share"
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("결제 수단 컬럼을 찾을 수 없습니다.")

with row3_col2:
    st.subheader("🔍 필터링 데이터 샘플")
    st.dataframe(filtered_df.head(10), use_container_width=True)