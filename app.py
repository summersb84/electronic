import itertools
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="Electronic Sales Dashboard", page_icon="📊", layout="wide"
)


# 2. 데이터 로드 및 전처리 함수
@st.cache_data
def load_and_preprocess_data(file_path):
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.strip()

    date_col = [col for col in df.columns if "date" in col.lower()]
    if date_col:
        df[date_col[0]] = pd.to_datetime(df[date_col[0]], errors="coerce")
        df["YearMonth"] = df[date_col[0]].dt.to_period("M").astype(str)
        df["Month"] = df[date_col[0]].dt.month
        df["DayOfWeek"] = df[date_col[0]].dt.day_name()

    cols_lower = {col.lower(): col for col in df.columns}
    if "total price" not in cols_lower and "total_amount" not in cols_lower:
        price_col = [c for c in df.columns if "price" in c.lower()]
        qty_col = [
            c
            for c in df.columns
            if "quantity" in c.lower() or "qty" in c.lower()
        ]
        if price_col and qty_col:
            df["Total Sales"] = df[price_col[0]] * df[qty_col[0]]
    else:
        sales_col = cols_lower.get("total price") or cols_lower.get(
            "total_amount"
        )
        df["Total Sales"] = df[sales_col]

    df = df.dropna(subset=["Total Sales"])
    return df


# 지정하신 데이터 파일명 적용
DATA_PATH = "Electronic_sales_Sep2023-Sep2024.csv"

try:
    df = load_and_preprocess_data(DATA_PATH)
except Exception as e:
    st.error(
        f"데이터 파일('{DATA_PATH}')을 로드하는 중 오류가 발생했습니다. 저장소에 파일이 존재하는지 확인해 주세요."
    )
    st.stop()

# ---------------------------------------------------------
# [사이드바] 날짜 필터링
# ---------------------------------------------------------
st.sidebar.header("🔍 데이터 필터")

date_cols = [col for col in df.columns if "date" in col.lower()]
date_col_name = date_cols[0] if date_cols else None

if date_col_name and pd.api.types.is_datetime64_any_dtype(df[date_col_name]):
    min_date = df[date_col_name].min().date()
    max_date = df[date_col_name].max().date()

    selected_date_range = st.sidebar.date_input(
        "📅 조회 기간 선택",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date,
    )

    if (
        isinstance(selected_date_range, tuple)
        and len(selected_date_range) == 2
    ):
        start_date, end_date = selected_date_range
        filtered_df = df[
            (df[date_col_name].dt.date >= start_date)
            & (df[date_col_name].dt.date <= end_date)
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
user_cols = [
    c
    for c in filtered_df.columns
    if "customer" in c.lower() or "user" in c.lower() or "client" in c.lower()
]
cust_col = user_cols[0] if user_cols else None

# === KPI 주요 지표 계산 ===
total_revenue = filtered_df["Total Sales"].sum()
total_orders = len(filtered_df)
avg_order_value = total_revenue / total_orders if total_orders > 0 else 0

if cust_col and cust_col in filtered_df.columns:
    total_customers = filtered_df[cust_col].nunique()
    arpu = (
        total_revenue / total_customers if total_customers > 0 else 0
    )  # 인당 객단가

    # 재구매율 계산 (2회 이상 구매 고객 비율)
    order_counts_per_cust = filtered_df.groupby(cust_col).size()
    repeat_customers = (order_counts_per_cust >= 2).sum()
    repeat_rate = (
        (repeat_customers / total_customers * 100) if total_customers > 0 else 0
    )
else:
    total_customers = 0
    arpu = 0
    repeat_rate = 0

# === KPI Row 1: 기본 실적 지표 ===
kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
kpi_col1.metric("총 매출액 (Total Revenue)", f"${total_revenue:,.2f}")
kpi_col2.metric("총 주문 건수 (Total Orders)", f"{total_orders:,} 건")
kpi_col3.metric("평균 주문 금액 (건당)", f"${avg_order_value:,.2f}")

st.markdown(
    "<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True
)  # 줄간격 여백

# === KPI Row 2: 고객 관점 지표 ===
kpi_col4, kpi_col5, kpi_col6 = st.columns(3)

if cust_col:
    kpi_col4.metric(
        label="총 주문 고객수 (Total Customers)",
        value=f"{total_customers:,} 명",
        help="선택된 집계 기간 동안 1회 이상 구매 이력이 있는 고유 고객(Customer ID 기준) 수입니다.",
    )

    kpi_col5.metric(
        label="인당 객단가 (ARPU)",
        value=f"${arpu:,.2f}",
        help="고객 1인당 평균 결제 금액입니다. (산출식: 총 매출액 ÷ 총 주문 고객수)",
    )

    kpi_col6.metric(
        label="재구매율 (Repeat Purchase Rate)",
        value=f"{repeat_rate:.1f}%",
        help="전체 구매 고객 중 2회 이상 주문한 고객의 비중입니다. (산출식: 2회 이상 주문 고객수 ÷ 총 주문 고객수 × 100)",
    )
else:
    kpi_col4.metric("총 주문 고객수", "N/A")
    kpi_col5.metric("인당 객단가", "N/A")
    kpi_col6.metric("재구매율", "N/A")

# 하단 텍스트 설명 보완 (지표 바로 아래에 표시)
st.caption(
    "💡 **지표 정의 및 산출 안내** | "
    "**건당 평균 금액**: 1회 주문 기준 평균 결제액 | "
    "**인당 객단가**: 고객 1명이 기간 내 기여한 총 매출 | "
    "**재구매율**: 기간 내 2회 이상 재주문한 리텐션 고객 비중"
)

st.markdown("---")

# ---------------------------------------------------------
# 4. 시각화 차트 구성 (메인 배치)
# ---------------------------------------------------------

col_left, col_right = st.columns([1.2, 0.8])

# === [좌측 컬럼] 통합 월별 매출 및 구매자 추이 ===
with col_left:
    st.subheader("📈 월별 매출 및 구매자 추이 (통합)")

    user_cols = [
        c
        for c in filtered_df.columns
        if "customer" in c.lower()
        or "user" in c.lower()
        or "client" in c.lower()
    ]

    if "YearMonth" in filtered_df.columns and user_cols:
        cust_col = user_cols[0]

        # 월별 매출 및 구매자 수 데이터 집계
        monthly_df = (
            filtered_df.groupby("YearMonth")
            .agg(
                Sales=("Total Sales", "sum"),
                Active_Users=(cust_col, "nunique"),
            )
            .reset_index()
        )

        # 이중 축(Secondary Y-axis) 그래프 생성
        fig_combined = make_subplots(specs=[[{"secondary_y": True}]])

        # 1) 매출액 (좌측 Y축 - 막대 그래프)
        fig_combined.add_trace(
            go.Bar(
                x=monthly_df["YearMonth"],
                y=monthly_df["Sales"],
                name="매출액 ($)",
                marker_color="#636EFA",
                opacity=0.75,
            ),
            secondary_y=False,
        )

        # 2) 구매자 수 (우측 Y축 - 꺾은선 그래프)
        fig_combined.add_trace(
            go.Scatter(
                x=monthly_df["YearMonth"],
                y=monthly_df["Active_Users"],
                name="구매자 수 (명)",
                mode="lines+markers",
                line=dict(color="#EF553B", width=3),
                marker=dict(size=7),
            ),
            secondary_y=True,
        )

        # 축 레이블 및 레이아웃 설정
        fig_combined.update_layout(
            title_text="Monthly Revenue & Active Customers Trend",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
            ),
        )
        fig_combined.update_yaxes(
            title_text="<b>매출액 ($)</b>", secondary_y=False
        )
        fig_combined.update_yaxes(
            title_text="<b>구매자 수 (명)</b>", secondary_y=True
        )

        st.plotly_chart(fig_combined, use_container_width=True)

        # --- 인사이트 섹션 ---
        if not monthly_df.empty:
            max_sales_row = monthly_df.loc[monthly_df["Sales"].idxmax()]
            max_users_row = monthly_df.loc[monthly_df["Active_Users"].idxmax()]

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

    loyalty_cols = [
        c
        for c in filtered_df.columns
        if "loyalty" in c.lower() or "member" in c.lower()
    ]

    if loyalty_cols:
        loyalty_col = loyalty_cols[0]
        loyalty_summary = (
            filtered_df.groupby(loyalty_col)
            .agg(
                Total_Sales=("Total Sales", "sum"),
                Order_Count=("Total Sales", "count"),
            )
            .reset_index()
        )

        fig_loyalty = px.pie(
            loyalty_summary,
            names=loyalty_col,
            values="Total_Sales",
            hole=0.4,
            title=f"Sales Share by {loyalty_col}",
            color_discrete_sequence=px.colors.qualitative.Set2,
        )
        st.plotly_chart(fig_loyalty, use_container_width=True)

        # --- 인사이트 섹션 ---
        if not loyalty_summary.empty:
            loyalty_summary["Sales_Share"] = (
                loyalty_summary["Total_Sales"]
                / loyalty_summary["Total_Sales"].sum()
            ) * 100
            top_member = loyalty_summary.loc[
                loyalty_summary["Total_Sales"].idxmax()
            ]

            st.info(
                f"💡 **Loyalty 인사이트**\n"
                f"- **최대 매출 기여 그룹:** '{top_member[loyalty_col]}' ({top_member['Sales_Share']:.1f}% 점유)\n"
                f"- 로열티 회원과 비회원의 매출 비중 구조를 파악하여 회원제 리텐션 프로모션 전략 수립에 활용할 수 있습니다."
            )
    else:
        st.info("Loyalty Member 관련 컬럼을 찾을 수 없습니다.")

st.markdown("---")

# ---------------------------------------------------------
# 4. 제품별 매출 및 제품 교차 구매(Cross-selling) 분석
# ---------------------------------------------------------
st.header("📦 제품별 매출 및 교차 구매 분석 (Product Sales & Cross-Selling)")

prod_cols = [
    c
    for c in filtered_df.columns
    if "product" in c.lower() or "item" in c.lower() or "goods" in c.lower()
]
order_cols = [
    c
    for c in filtered_df.columns
    if "order" in c.lower()
    or "invoice" in c.lower()
    or "transaction" in c.lower()
]
cust_cols = [
    c
    for c in filtered_df.columns
    if "customer" in c.lower() or "user" in c.lower()
]

prod_col = prod_cols[0] if prod_cols else None
order_col = (
    order_cols[0] if order_cols else (cust_cols[0] if cust_cols else None)
)

col_chart1, col_chart2 = st.columns(2)

# === 1) 제품별 매출 분석 (Bar Chart) ===
with col_chart1:
    st.subheader("📊 제품별 매출 순위 (Product Sales)")
    if prod_col and "Total Sales" in filtered_df.columns:
        prod_sales = (
            filtered_df.groupby(prod_col)["Total Sales"]
            .sum()
            .reset_index()
            .sort_values(by="Total Sales", ascending=True)
        )

        if len(prod_sales) > 15:
            prod_sales = prod_sales.tail(15)

        fig_prod_sales = px.bar(
            prod_sales,
            x="Total Sales",
            y=prod_col,
            orientation="h",
            title="Top Selling Products by Revenue",
            labels={"Total Sales": "총 매출액 ($)", prod_col: "제품명"},
            text_auto=",.0f",
            color="Total Sales",
            color_continuous_scale="Blues",
        )
        fig_prod_sales.update_layout(
            coloraxis_showscale=False,
            height=450,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_prod_sales, use_container_width=True)
    else:
        st.warning(
            "제품명(Product) 및 매출(Total Sales) 컬럼을 찾을 수 없습니다."
        )

# === 2) 제품 교차 구매 분석 (Cross-Selling Heatmap) ===
with col_chart2:
    st.subheader("🔄 제품 간 교차 구매 빈도 (Cross-Selling)")
    if prod_col and order_col:
        order_prod_df = filtered_df[[order_col, prod_col]].drop_duplicates()

        order_counts = order_prod_df.groupby(order_col)[prod_col].nunique()
        multi_item_orders = order_counts[order_counts > 1].index
        filtered_multi = order_prod_df[
            order_prod_df[order_col].isin(multi_item_orders)
        ]

        if not filtered_multi.empty:
            grouped_orders = filtered_multi.groupby(order_col)[prod_col].apply(
                list
            )

            pair_counts = {}
            for items in grouped_orders:
                for p1, p2 in itertools.combinations(sorted(set(items)), 2):
                    pair_counts[(p1, p2)] = pair_counts.get((p1, p2), 0) + 1
                    pair_counts[(p2, p1)] = pair_counts.get((p2, p1), 0) + 1

            unique_products = sorted(filtered_multi[prod_col].unique())
            matrix_df = pd.DataFrame(
                0, index=unique_products, columns=unique_products
            )

            for (p1, p2), count in pair_counts.items():
                if p1 in matrix_df.index and p2 in matrix_df.columns:
                    matrix_df.loc[p1, p2] = count

            fig_cross = px.imshow(
                matrix_df,
                labels=dict(
                    x="함께 구매된 제품 B",
                    y="기준 제품 A",
                    color="동시 구매 건수",
                ),
                x=matrix_df.columns,
                y=matrix_df.index,
                color_continuous_scale="Purples",
                aspect="auto",
                title="Product Co-occurrence Matrix",
                text_auto=True,
            )
            fig_cross.update_layout(
                height=450, margin=dict(l=10, r=10, t=40, b=10)
            )
            st.plotly_chart(fig_cross, use_container_width=True)

        else:
            st.info(
                "💡 동일 주문 내 2개 이상의 서로 다른 제품을 구매한 이력이 없어 교차 구매 히트맵을 생성할 수 없습니다."
            )
    else:
        st.warning(
            "교차 구매 분석을 위한 식별자(Order/Customer ID) 또는 제품(Product) 컬럼이 부족합니다."
        )

# ---------------------------------------------------------
# 제품 분석 하단: 상위 Top 5 제품 월별 매출 추이 (Time-Series Line Chart)
# ---------------------------------------------------------
st.markdown("---")
st.markdown(
    "#### 📈 상위 Top 5 제품 월별 매출 추이 (Product Monthly Revenue Trend)"
)

date_cols = [c for c in filtered_df.columns if "date" in c.lower()]
prod_cols = [
    c
    for c in filtered_df.columns
    if "prod" in c.lower() or "item" in c.lower() or "name" in c.lower()
]

if date_cols and prod_cols and "Total Sales" in filtered_df.columns:
    date_col = date_cols[0]
    prod_col = prod_cols[0]

    ts_df = filtered_df.copy()
    ts_df["YearMonth"] = ts_df[date_col].dt.to_period("M").astype(str)

    top5_products = (
        ts_df.groupby(prod_col)["Total Sales"]
        .sum()
        .nlargest(5)
        .index.tolist()
    )

    ts_top5 = ts_df[ts_df[prod_col].isin(top5_products)]
    monthly_trend = (
        ts_top5.groupby(["YearMonth", prod_col])["Total Sales"]
        .sum()
        .reset_index()
    )

    fig_line = px.line(
        monthly_trend,
        x="YearMonth",
        y="Total Sales",
        color=prod_col,
        markers=True,
        title="Monthly Sales Trend for Top 5 Products",
        labels={
            "YearMonth": "연월 (Year-Month)",
            "Total Sales": "매출액 ($)",
            prod_col: "제품명",
        },
    )

    fig_line.update_layout(
        height=420,
        xaxis_title="연월",
        yaxis_title="총 매출액 ($)",
        legend_title="상위 제품명",
        margin=dict(l=10, r=10, t=50, b=10),
    )

    st.plotly_chart(fig_line, use_container_width=True)

else:
    st.warning(
        "시계열 분석을 위한 날짜(Date), 제품명, 매출액 컬럼을 찾을 수 없습니다."
    )

오류의 핵심 원인은 with col_demo2: 블록 안의 들여쓰기(Indentation) 오류와 줄바꿈 문자/특수 공백(NBSP) 문제입니다.

with col_demo2: 내부에서 3D/지역 차트를 그린 직후 들여쓰기가 계속 유지된 채로 아래의 st.markdown("#### ⚖️ 세그먼트별 고객 수...") 이하 전체 로직이 우측 컬럼 안에 갇혀버렸고, 이 때문에 if-else 구조가 꼬여 구문 오류(SyntaxError 또는 IndentationError)가 발생했습니다.

또한, 보이지 않는 줄바꿈/특수 공백 문자가 섞여 있어 파이썬 인터프리터가 들여쓰기를 인식하지 못했던 문제입니다.

🛠️ 수정 완료된 전체 코드
인구통계학 좌우 차트 배치는 깔끔하게 완료하고, 그 밑에 세그먼트별 매출 기여도 비교 차트, 동적 인사이트, 상세 데이터표가 화면 전체 너비로 시원하게 이어지도록 들여쓰기를 올바르게 정돈한 코드입니다.

Python
import plotly.express as px
import streamlit as st

# ---------------------------------------------------------
# 5. 인구통계학(Demographics) 기반 고객 분석
# ---------------------------------------------------------
st.markdown("---")
st.header("👥 고객 인구통계학 분석 (Demographic Analysis)")

col_demo1, col_demo2 = st.columns(2)

# === [좌측] 연령대 및 성별 고객 분포 ===
with col_demo1:
    st.subheader("📊 연령대 및 성별 고객 비중")

    # 데이터 컬럼 자동 탐색 (Age, Gender)
    age_col = [c for c in filtered_df.columns if "age" in c.lower()]
    gender_col = [
        c
        for c in filtered_df.columns
        if "gender" in c.lower() or "sex" in c.lower()
    ]

    if age_col and gender_col:
        demo_df = (
            filtered_df.groupby([age_col[0], gender_col[0]])
            .size()
            .reset_index(name="Customer_Count")
        )

        fig_demo = px.bar(
            demo_df,
            x=age_col[0],
            y="Customer_Count",
            color=gender_col[0],
            barmode="group",
            title="Customer Count by Age Group & Gender",
            labels={
                age_col[0]: "연령대",
                "Customer_Count": "고객 수(명)",
                gender_col[0]: "성별",
            },
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_demo.update_layout(height=400, margin=dict(l=10, r=10, t=40, b=10))
        st.plotly_chart(fig_demo, use_container_width=True)
    else:
        st.info(
            "데이터셋 내에 연령(Age) 또는 성별(Gender) 관련 컬럼이 없어 표시할 수 없습니다."
        )

# === [우측] 거주 지역/채널별 고객 분포 ===
with col_demo2:
    st.subheader("📍 지역/채널별 고객 분포")

    loc_col = [
        c
        for c in filtered_df.columns
        if "region" in c.lower()
        or "city" in c.lower()
        or "state" in c.lower()
        or "location" in c.lower()
    ]

    if loc_col:
        loc_df = (
            filtered_df.groupby(loc_col[0])
            .size()
            .reset_index(name="Customer_Count")
            .sort_values(by="Customer_Count", ascending=True)
        )

        fig_loc = px.bar(
            loc_df.tail(10),  # 상위 10개 지역
            x="Customer_Count",
            y=loc_col[0],
            orientation="h",
            title="Top Customer Distribution by Region",
            labels={"Customer_Count": "고객 수(명)", loc_col[0]: "지역"},
            color="Customer_Count",
            color_continuous_scale="Purples",
        )
        fig_loc.update_layout(
            coloraxis_showscale=False,
            height=400,
            margin=dict(l=10, r=10, t=40, b=10),
        )
        st.plotly_chart(fig_loc, use_container_width=True)
    else:
        st.info(
            "데이터셋 내에 지역(Region/Location) 관련 컬럼이 없어 표시할 수 없습니다."
        )

# ---------------------------------------------------------
# 6. 세그먼트별 고객 수 vs 매출 기여도 비중 비교 (Pareto Analysis)
# ---------------------------------------------------------
# ※ with col_demo2 블록 밖으로 빠져나와 전체 화면 너비를 사용합니다.
st.markdown("---")
st.markdown(
    "#### ⚖️ 세그먼트별 고객 수 vs 매출 기여도 비중 비교 (Pareto Analysis)"
)

# RFM 데이터가 존재하는지 검증 후 차트 생성
if "rfm_df" in locals() and not rfm_df.empty:
    segment_summary = (
        rfm_df.groupby("Segment")
        .agg(
            Customer_Count=(cust_col, "count"),
            Total_Revenue=("Monetary", "sum"),
        )
        .reset_index()
    )

    total_customers = segment_summary["Customer_Count"].sum()
    total_revenue = segment_summary["Total_Revenue"].sum()

    segment_summary["Customer_Share"] = (
        segment_summary["Customer_Count"] / total_customers
    ) * 100
    segment_summary["Revenue_Share"] = (
        segment_summary["Total_Revenue"] / total_revenue
    ) * 100

    comparison_melted = segment_summary.melt(
        id_vars=["Segment"],
        value_vars=["Customer_Share", "Revenue_Share"],
        var_name="Metric",
        value_name="Percentage",
    )

    comparison_melted["Metric"] = comparison_melted["Metric"].map(
        {"Customer_Share": "고객 수 비중 (%)", "Revenue_Share": "매출 기여도 비중 (%)"}
    )

    segment_order = [
        "Hibernating (휴면 유저)",
        "New Customers (신규)",
        "At-Risk (이탈 위험군)",
        "Loyal Customers",
        "VIP (Champs)",
    ]

    fig_compare = px.bar(
        comparison_melted,
        x="Segment",
        y="Percentage",
        color="Metric",
        barmode="group",
        title="Customer Share vs Revenue Share by Segment",
        labels={
            "Segment": "고객 세그먼트",
            "Percentage": "비중 (%)",
            "Metric": "구분",
        },
        text_auto=".1f",
        color_discrete_sequence=["#9467bd", "#1f77b4"],
    )

    fig_compare.update_layout(
        height=360,
        yaxis=dict(title="비중 (%)", range=[0, 100]),
        xaxis=dict(categoryorder="array", categoryarray=segment_order),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
        ),
        margin=dict(l=10, r=10, t=50, b=10),
    )

    st.plotly_chart(fig_compare, use_container_width=True)

    # ---------------------------------------------------------
    # 7. 동적 인사이트 및 세그먼트별 마케팅 액션 플랜
    # ---------------------------------------------------------
    at_risk_row = segment_summary[
        segment_summary["Segment"] == "At-Risk (이탈 위험군)"
    ]
    vip_row = segment_summary[segment_summary["Segment"] == "VIP (Champs)"]

    at_risk_rev_share = (
        at_risk_row["Revenue_Share"].values[0] if not at_risk_row.empty else 0
    )
    at_risk_cust_cnt = (
        at_risk_row["Customer_Count"].values[0] if not at_risk_row.empty else 0
    )
    vip_rev_share = (
        vip_row["Revenue_Share"].values[0] if not vip_row.empty else 0
    )

    st.subheader("💡 Key Insights & Target Marketing Strategy")

    col_ins1, col_ins2 = st.columns(2)

    with col_ins1:
        st.markdown(
            f"""
        <div style="background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #d62728; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #d62728;">🚨 이탈 위험군 (At-Risk) 긴급 대응 필요</h4>
            <p style="font-size: 14px; margin-top: 8px; color: #333;">
                • <b>매출 방어 관점:</b> 과거 기여도가 높았으나 최근 방문이 끊긴 <b>At-Risk 그룹이 전체 매출의 {at_risk_rev_share:.1f}%</b>를 차지합니다.<br>
                • <b>액션 플랜:</b> {at_risk_cust_cnt:,}명의 유저를 대상으로 <b>"복귀 전용 할인 쿠폰" 및 연관 상품 재추천 CRM 메시지</b>를 발송하여 리텐션을 회복해야 합니다.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
        <div style="background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #1f77b4; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #1f77b4;">👑 VIP & Loyal 유저 매출 락인(Lock-in)</h4>
            <p style="font-size: 14px; margin-top: 8px; color: #333;">
                • <b>매출 집중도:</b> VIP 유저군이 전체 매출의 <b>{vip_rev_share:.1f}%</b>를 견인하는 핵심 자산입니다.<br>
                • <b>액션 플랜:</b> 신제품 우선 체험권, VIP 전용 무료 배송 및 리워드 프로그램 강화를 통해 타사 이탈을 방지합니다.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with col_ins2:
        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #ff7f0e; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #ff7f0e;">🌱 New Customers 2차 구매 유도</h4>
            <p style="font-size: 14px; margin-top: 8px; color: #333;">
                • <b>전환 관점:</b> 최근 신규 유입된 유저들은 1회 구매에 그칠 가능성이 높습니다.<br>
                • <b>액션 플랜:</b> 첫 구매 후 7일 이내 사용 가능한 <b>"2차 구매 웰컴 혜택" 및 온보딩 모바일 푸시</b>로 LTV(고객 생애 가치)를 극대화해야 합니다.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

        st.markdown(
            """
        <div style="background-color: #f8f9fa; padding: 18px; border-radius: 8px; border-left: 5px solid #7f7f7f; margin-bottom: 15px;">
            <h4 style="margin: 0; color: #555;">💤 휴면 유저 (Hibernating) 비용 효율화</h4>
            <p style="font-size: 14px; margin-top: 8px; color: #333;">
                • <b>비용 관리:</b> 오래전 소액 구매 후 반응이 없는 유저층입니다.<br>
                • <b>액션 플랜:</b> 무분별한 유상 타깃 마케팅을 지양하고, 대형 시즌 프로모션(예: 블랙프라이데이) 때만 제한적으로 재활성화 메일을 발송합니다.
            </p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    # ---------------------------------------------------------
    # 8. 세그먼트별 상세 데이터표 (Expander)
    # ---------------------------------------------------------
    with st.expander("📋 세그먼트별 상세 지표 데이터표 확인하기"):
        display_rfm = (
            rfm_df.groupby("Segment")
            .agg(
                Customer_Count=(cust_col, "count"),
                Total_Monetary=("Monetary", "sum"),
                Avg_Recency=("Recency", "mean"),
                Avg_Frequency=("Frequency", "mean"),
                Avg_Monetary=("Monetary", "mean"),
            )
            .reset_index()
        )

        display_rfm["Cust_Share (%)"] = (
            display_rfm["Customer_Count"] / total_customers
        ) * 100
        display_rfm["Revenue_Share (%)"] = (
            display_rfm["Total_Monetary"] / total_revenue
        ) * 100

        display_rfm = display_rfm[
            [
                "Segment",
                "Customer_Count",
                "Cust_Share (%)",
                "Total_Monetary",
                "Revenue_Share (%)",
                "Avg_Recency",
                "Avg_Frequency",
                "Avg_Monetary",
            ]
        ]
        display_rfm.columns = [
            "세그먼트",
            "고객수(명)",
            "고객비중(%)",
            "총매출($)",
            "매출점유율(%)",
            "평균최근성(일)",
            "평균구매(회)",
            "평균구매액($)",
        ]

        st.dataframe(
            display_rfm.style.format(
                {
                    "고객수(명)": "{:,}",
                    "고객비중(%)": "{:.1f}%",
                    "총매출($)": "${:,.2f}",
                    "매출점유율(%)": "{:.1f}%",
                    "평균최근성(일)": "{:.1f}",
                    "평균구매(회)": "{:.1f}",
                    "평균구매액($)": "${:,.2f}",
                }
            ),
            use_container_width=True,
        )

else:
    st.warning(
        "RFM 분석을 수행하기 위한 필수 컬럼(고객 ID, 날짜, 매출액)을 찾을 수 없거나 데이터가 비어있습니다."
    )