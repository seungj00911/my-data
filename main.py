import streamlit as st
import pandas as pd
import altair as alt

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 기온 데이터 분석",
    layout="wide"
)

st.title("서울의 100년간 연평균 기온 변화")

st.write(
    "서울의 기온 데이터를 이용하여 연도별 연평균 기온의 변화와 "
    "원본 데이터의 요약통계를 확인합니다."
)


@st.cache_data
def load_data():
    df = pd.read_csv(DATA_URL)

    df["날짜"] = pd.to_datetime(df["날짜"], errors="coerce")
    df["연도"] = df["날짜"].dt.year

    # 연도별 연평균 기온
    yearly = (
        df.groupby("연도")["평균기온"]
        .mean()
        .reset_index()
    )

    return df, yearly


df, yearly_data = load_data()


# =========================
# 원본 데이터 요약통계
# =========================

st.subheader("원본 데이터 요약통계")

summary = df[
    ["평균기온", "최저기온", "최고기온"]
].describe()

summary = summary.rename(
    index={
        "count": "개수",
        "mean": "평균",
        "std": "표준편차",
        "min": "최소",
        "25%": "1사분위수",
        "50%": "중앙값",
        "75%": "3사분위수",
        "max": "최대"
    }
)

st.dataframe(
    summary.round(2),
    use_container_width=True
)


# =========================
# 연도별 데이터 확인
# =========================

st.subheader("연도별 연평균 기온 변화")

min_year = int(df["연도"].min())
max_year = int(df["연도"].max())

# 모든 연도를 만들어 데이터가 없는 연도도 확인
all_years = pd.DataFrame({
    "연도": range(min_year, max_year + 1)
})

yearly_data = all_years.merge(
    yearly_data,
    on="연도",
    how="left"
)

yearly_data = yearly_data.rename(
    columns={"평균기온": "연평균기온"}
)


# =========================
# 이상 연도 판별
# =========================

overall_mean = yearly_data["연평균기온"].mean()
overall_std = yearly_data["연평균기온"].std()

low_threshold = overall_mean - (2 * overall_std)

yearly_data["상태"] = "정상"

# 데이터가 없는 연도
yearly_data.loc[
    yearly_data["연평균기온"].isna(),
    "상태"
] = "데이터 없음"

# 유난히 낮은 연도
yearly_data.loc[
    yearly_data["연평균기온"] < low_threshold,
    "상태"
] = "유난히 낮음"


# =========================
# 그래프
# =========================

base = alt.Chart(yearly_data).encode(
    x=alt.X(
        "연도:O",
        title="연도",
        axis=alt.Axis(labelAngle=-45)
    ),
    y=alt.Y(
        "연평균기온:Q",
        title="연평균 기온 (℃)"
    )
)

# 기본 선
line = base.mark_line()

# 정상 연도
normal = (
    base.transform_filter(
        alt.datum.상태 == "정상"
    )
    .mark_circle(size=30)
)

# 이상 연도
abnormal = (
    base.transform_filter(
        alt.datum.상태 != "정상"
    )
    .mark_circle(size=120)
    .encode(
        color=alt.Color(
            "상태:N",
            scale=alt.Scale(
                domain=["데이터 없음", "유난히 낮음"],
                range=["red", "orange"]
            ),
            legend=alt.Legend(title="상태")
        ),
        tooltip=[
            alt.Tooltip("연도:O", title="연도"),
            alt.Tooltip(
                "연평균기온:Q",
                title="연평균 기온",
                format=".2f"
            ),
            alt.Tooltip("상태:N", title="상태")
        ]
    )
)

chart = (
    line + normal + abnormal
).properties(
    height=500
)

st.altair_chart(
    chart,
    use_container_width=True
)

st.caption(
    "빨간색: 해당 연도의 데이터 없음 / "
    "주황색: 유난히 낮은 연평균 기온"
)


# =========================
# 이상 연도 목록
# =========================

abnormal_data = yearly_data[
    yearly_data["상태"] != "정상"
][["연도", "연평균기온", "상태"]].copy()

if len(abnormal_data) > 0:
    st.subheader("확인이 필요한 연도")

    abnormal_data["연평균기온"] = (
        abnormal_data["연평균기온"].round(2)
    )

    st.dataframe(
        abnormal_data,
        use_container_width=True,
        hide_index=True
    )


# =========================
# 데이터 기본 정보
# =========================

st.subheader("데이터 기본 정보")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "전체 데이터 개수",
        f"{len(df):,}개"
    )

with col2:
    st.metric(
        "분석 시작 연도",
        f"{min_year}년"
    )

with col3:
    st.metric(
        "분석 종료 연도",
        f"{max_year}년"
    )
