import numpy as np
import pandas as pd

# 1. 원본 데이터 로드 (실제 Kaggle csv 파일 경로로 지정)
raw_df = pd.read_csv("Electronic_sales_Sep2023-Sep2024.csv")

# [시연용] Kaggle 데이터셋 구조를 모방한 가상 데이터 생성
np.random.seed(42)
n_rows = 1000

raw_df = pd.DataFrame(
    {
        "Order_ID": [f"ORD-{10000+i}" for i in range(n_rows)],
        "Purchase_Date": pd.date_range(
            start="2025-01-01", periods=n_rows, freq="h"
        ),
        "Product_Category": np.random.choice(
            ["Smartphones", "Laptops", "Smart TVs", "Appliances", "Wearables"],
            n_rows,
        ),
        "Product_Name": np.random.choice(
            [
                "Galaxy S24 Ultra",
                "Galaxy Z Flip6",
                "Galaxy Book4 Pro",
                "Neo QLED 8K",
                "Bespoke Grand AI",
                "Galaxy Watch6",
            ],
            n_rows,
        ),
        "Unit_Price": np.random.choice(
            [350000, 850000, 1450000, 2100000, 3200000], n_rows
        ),
        "Quantity": np.random.choice([1, 2, 3], n_rows, p=[0.85, 0.10, 0.05]),
        "Store_Location": np.random.choice(
            ["Seoul_South", "Seoul_North", "Gyeonggi", "Busan", "Daegu"], n_rows
        ),
        "Customer_Age": np.random.randint(20, 70, n_rows),
        "Add_ons_Purchased": np.random.choice(
            ["Warranty", "Accessory", "Both", "None"],
            n_rows,
            p=[0.30, 0.25, 0.20, 0.25],
        ),
        "Customer_Segment": np.random.choice(
            ["BLUE", "SILVER", "GOLD", "VIP"], n_rows, p=[0.4, 0.3, 0.2, 0.1]
        ),
    }
)


# 2. 삼성전자판매 전용 데이터 변환 함수
def transform_to_samsung_sales(df):
    data = df.copy()

    # (1) 해외 지점명을 삼성스토어 실제 권역 및 지점명으로 매핑
    store_map = {
        "Seoul_South": ("수도권", "삼성스토어 강남"),
        "Seoul_North": ("수도권", "삼성스토어 홍대"),
        "Gyeonggi": ("수도권", "삼성스토어 판교"),
        "Busan": ("영남권", "삼성스토어 부산본점"),
        "Daegu": ("영남권", "삼성스토어 동대구"),
    }
    data["권역"] = data["Store_Location"].map(
        lambda x: store_map.get(x, ("기타", "삼성스토어 기타"))[0]
    )
    data["지점명"] = data["Store_Location"].map(
        lambda x: store_map.get(x, ("기타", "삼성스토어 기타"))[1]
    )

    # (2) 상품 카테고리 삼성스토어 분류체계 표준화
    category_map = {
        "Smartphones": "모바일",
        "Wearables": "모바일/웨어러블",
        "Laptops": "PC/태블릿",
        "Smart TVs": "TV/AV",
        "Appliances": "주방/생활가전",
    }
    data["카테고리"] = (
        data["Product_Category"].map(category_map).fillna("기타가전")
    )

    # (3) 핵심 KPI: 삼성케어플러스 및 연계 상품(액세서리) 동시 구매 여부 생성
    data["삼성케어플러스_가입"] = data["Add_ons_Purchased"].isin(
        ["Warranty", "Both"]
    )
    data["액세서리_동시구매"] = data["Add_ons_Purchased"].isin(
        ["Accessory", "Both"]
    )
    data["연계판매_성공여부"] = (
        data["삼성케어플러스_가입"] | data["액세서리_동시구매"]
    )

    # (4) 매출액 및 추정 영업이익 계산 (카테고리별 마진율 반영)
    data["총매출액"] = data["Unit_Price"] * data["Quantity"]
    margin_rates = {
        "모바일": 0.12,
        "모바일/웨어러블": 0.15,
        "PC/태블릿": 0.10,
        "TV/AV": 0.18,
        "주방/생활가전": 0.22,
    }
    data["추정마진율"] = data["카테고리"].map(margin_rates).fillna(0.15)
    data["추정영업이익"] = data["총매출액"] * data["추정마진율"]

    # (5) 연령대 세그먼트 생성
    data["연령대"] = pd.cut(
        data["Customer_Age"],
        bins=[0, 29, 39, 49, 59, 100],
        labels=["20대 이하", "30대", "40대", "50대", "60대 이상"],
    )

    # (6) 컬럼명 한글화 및 정리
    data.rename(
        columns={
            "Purchase_Date": "결제일시",
            "Product_Name": "제품명",
            "Unit_Price": "단가",
            "Quantity": "수량",
            "Customer_Segment": "삼성멤버십등급",
        },
        inplace=True,
    )

    target_cols = [
        "Order_ID",
        "결제일시",
        "권역",
        "지점명",
        "카테고리",
        "제품명",
        "단가",
        "수량",
        "총매출액",
        "추정영업이익",
        "삼성케어플러스_가입",
        "액세서리_동시구매",
        "연계판매_성공여부",
        "삼성멤버십등급",
        "연령대",
    ]

    return data[target_cols]


# 3. 데이터 변환 및 Streamlit용 데이터셋 저장
samsung_sales_df = transform_to_samsung_sales(raw_df)
samsung_sales_df.to_csv("samsung_store_sales_processed.csv", index=False)
print("변환 완료! 생성된 데이터 수:", len(samsung_sales_df))