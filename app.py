import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Electronic Sales Dashboard",
    page_icon="📊",
    layout="wide"
)

# 2. 데이터 로드 및 전처리 함수 (캐싱 적용)
@st.cache_data
def load_and_preprocess_data(file_path):
    # 데이터 불러오기
    df = pd.read_csv("Electronic_sales_Sep2023-Sep2024.csv")
    
    # [전처리 1] 컬럼명 정리 (공백 제거 및 소문자화/대문자 통일)
    df.columns = df.columns.str.strip()
    
    # [전처리 2] 날짜 데이터 형변환 (Order Date / Date 컬럼 대응)
    date_col = [col for col in df.columns if 'date' in col.lower()]
    if date_col:
        df[date_col[0]] = pd.to_datetime(df[date_col[0]], errors='coerce')
        # 연월/월 파생변수 생성
        df['YearMonth'] = df[date_col[0]].dt.to_period('M').astype(str)
        df['Month'] = df[date_col[0]].dt.month
        df['DayOfWeek'] = df[date_col[0]].dt.day_name()
    
    # [전처리 3] 수치형 컬럼 결측치 처리 및 계산
    # Total Price/Amount 컬럼이 없다면 Price * Quantity로 생성
    cols_lower = {col.lower(): col for col in df.columns}
    
    if 'total price' not in cols_lower and 'total_amount' not in cols_lower:
        price_col = [c for c in df.columns if 'price' in c.lower()]
        qty_col = [c for c in df.columns if 'quantity' in c.lower() or 'qty' in c.lower()]
        if price_col and qty_col:
            df['Total Sales'] = df[price_col[0]] * df[qty_col[0]]
    else:
        sales_col = cols_lower.get('total price') or cols_lower.get('total_amount')
        df['Total Sales'] = df[sales_col]
        
    # [전처리 4] 결측치 제거/대체
    df = df.dropna(subset=['Total Sales'])
    
    return df

# 데이터 불러오기 (파일명이 다를 경우 수정)
DATA_PATH = "Electronic_sales_Sep2023-Sep2024.csv" 

try:
    df = load_and_preprocess_data(DATA_PATH)
except Exception as e:
    st.error(f"데이터 파일('{DATA_PATH}')을 로드하는 중 오류가 발생했습니다. 저장소에 파일이 존재하는지 확인해 주세요.")
    st.stop()


# ---------------------------------------------------------
# 사이드바 (Sidebar) 필터 설정
# ---------------------------------------------------------
st.sidebar.header("🔍 데이터 필터")

date_cols = [col for col in df.columns if 'date' in col.lower()]
date_col_name = date_cols[0] if date_cols else None

if date_col_name and pd.api.types.is_datetime64_any_dtype(df[date_col_name]):
    min_date = df[date_col_name].min().date()
    max_date = df[date_col_name].max().date()

    # 날짜 범위 선택 위젯
    selected_date_range = st.sidebar.date_input(
        "📅 조회 기간 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # 선택된 범위로 데이터 필터링
    if isinstance(selected_date_range, tuple) and len(selected_date_range) == 2:
        start_date, end_date = selected_date_range
        filtered_df = df[
            (df[date_col_name].dt.date >= start_date) & 
            (df[date_col_name].dt.date <= end_date)
        ]
    else:
        filtered_df = df.copy()
else:
    filtered_df = df.copy()

# ---------------------------------------------------------
# 대시보드 헤더 및 주요 지표 (KPI) - filtered_df 적용
# ---------------------------------------------------------
st.title("⚡ Electronic Sales Data Dashboard")
st.markdown("전자기기 판매 데이터 전처리 및 핵심 시각화 대시보드")

# 선택된 기간 표시
if date_col_name and 'start_date' in locals():
    st.caption(f"📅 **현재 집계 기간:** {start_date} ~ {end_date}")
else:
    st.caption("📅 **현재 집계 기간:** 전체 기간")

st.markdown("---")

# 주요 지표 계산 (filtered_df 기준)
total_revenue = filtered_df['Total Sales'].sum()
total_orders = len(filtered_df)
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("총 매출액 (Total Revenue)", f"${total_revenue:,.2f}")
col2.metric("총 주문 건수 (Total Orders)", f"{total_orders:,} 건")
col3.metric("평균 주문 금액 (AOV)", f"${avg_order_value:,.2f}")

st.markdown("---")

# ※ 아래 차트 작성 시 df 대신 filtered_df를 사용하면 필터가 차트에 즉시 반영됩니다.


# 3. 대시보드 헤더 및 주요 지표(KPI)
st.title("⚡ Electronic Sales Data Dashboard")
st.markdown("전자기기 판매 데이터 전처리 및 핵심 시각화 대시보드")
st.markdown("---")

# --- [추가] 데이터 집계 기간 표기 ---
date_cols = [col for col in filtered_df를.columns if 'date' in col.lower()]
if date_cols and pd.api.types.is_datetime64_any_dtype(df[date_cols[0]]):
    start_date = filtered_df를[date_cols[0]].min().strftime('%Y-%m-%d')
    end_date = filtered_df를[date_cols[0]].max().strftime('%Y-%m-%d')
    st.caption(f"📅 **데이터 집계 기간:** {start_date} ~ {end_date}")
else:
    st.caption("📅 **데이터 집계 기간:** 전체 기간")

st.markdown("---")

# 주요 지표 계산
total_revenue = filtered_df를['Total Sales'].sum()
total_orders = len(filtered_df를)
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

col1, col2, col3 = st.columns(3)
col1.metric("총 매출액 (Total Revenue)", f"${total_revenue:,.2f}")
col2.metric("총 주문 건수 (Total Orders)", f"{total_orders:,} 건")
col3.metric("평균 주문 금액 (AOV)", f"${avg_order_value:,.2f}")

st.markdown("---")

# 4. 시각화 차트 구성
row1_col1, row1_col2 = st.columns(2)

# Chart 1: 월별 매출 추이
with row1_col1:
    st.subheader("📈 월별 매출 추이")
    if 'YearMonth' in filtered_df를.columns:
        monthly_sales = filtered_df를.groupby('YearMonth')['Total Sales'].sum().reset_index()
        fig_line = px.line(
            monthly_sales, 
            x='YearMonth', 
            y='Total Sales',
            markers=True,
            title="Monthly Sales Trend",
            labels={'YearMonth': '연월', 'Total Sales': '매출액 ($)'}
        )
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("날짜 컬럼을 찾을 수 없어 월별 추이를 표시하지 못했습니다.")

# Chart 2: 카테고리/제품별 매출 Top 10
with row1_col2:
    st.subheader("📦 카테고리/제품별 매출 Top 10")
    # Category 또는 Product Name 컬럼 탐색
    cat_cols = [c for c in df.columns if 'category' in c.lower() or 'product' in c.lower()]
    
    if cat_cols:
        target_cat = cat_cols[0]
        cat_sales = filtered_df를.groupby(target_cat)['Total Sales'].sum().reset_index()
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

row2_col1, row2_col2 = st.columns(2)

# Chart 3: 결제 수단 / 구매 유형 비중
with row2_col1:
    st.subheader("💳 결제 수단 비중")
    pay_cols = [c for c in df.columns if 'payment' in c.lower() or 'type' in c.lower()]
    
    if pay_cols:
        pay_df = filtered_df를[pay_cols[0]].value_counts().reset_index()
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

# Chart 4: 데이터 미리보기 (전처리 완료 데이터)
with row2_col2:
    st.subheader("🔍 전처리 데이터 샘플")
    st.dataframe(df.head(10), use_container_width=True)