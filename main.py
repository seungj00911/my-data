import streamlit as st
import pandas as pd

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 연평균 기온 변화",
    page_icon="🌡️",
    layout="wide"
)

st.title("서울의 100년간 연평균 기온 변화")
st.write("서울의 기온 데이터를 연도별로 집계하여 연평균 기온의 변화를 보여줍니다.")

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    # 날짜를 날짜 형식으로 변환
    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")

    # 연도 추출
    df["연도"] = df["날짜"].dt.year

    # 연평균 기온 계산
    yearly = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
        .dropna()
    )

    return yearly


try:
    yearly_data = load_data()

    st.subheader("연도별 평균기온")

    st.line_chart(
        yearly_data.set_index("연도")["평균기온"],
        height=500
    )

    st.caption("※ 세로축의 단위는 ℃이며, 각 연도의 일평균 기온을 평균하여 계산했습니다.")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "분석 시작 연도",
            f"{int(yearly_data['연도'].min())}년"
        )

    with col2:
        st.metric(
            "분석 종료 연도",
            f"{int(yearly_data['연도'].max())}년"
        )

    with col3:
        st.metric(
            "분석 연도 수",
            f"{len(yearly_data)}년"
        )

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.write(e)
  
