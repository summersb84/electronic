import streamlit as st

# 1. 상단 KPI 메트릭 (유통 현장 느낌 연출)
col1, col2, col3, col4 = st.columns(4)
col1.metric("전체 매출액", "₩12.4억", "+8.2%")
col2.metric("목표 달성률", "94.5%", "-1.5%")
col3.metric("케어플러스/액세서리 연계율", "38.2%", "+4.1%")
col4.metric("멤버십 고객 비율", "62.0%", "+2.3%")

# 2. 사이드바 필터 (매장/기간/카테고리)
st.sidebar.header("필터 조건")
selected_region = st.sidebar.multiselect("권역 선택", ["수도권", "영남권", "호남권", "충청권"])
selected_category = st.sidebar.selectbox("제품군", ["전체", "모바일/웨어러블", "TV/음향", "주방가전", "생활가전"])