import streamlit as st
import pandas as pd
import numpy as np
import altair as alt

DATA_URL = "https://raw.githubusercontent.com/greatsong/modudata/main/data/seoul.csv"

st.set_page_config(
    page_title="서울 기온 데이터 분석",
    page_icon="🌡️",
    layout="wide"
)

st.title("서울의 100년간 연평균 기온 변화")

st.write(
    "서울의 기온 데이터를 분석하여 연도별 연평균 기온의 변화와 "
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


try:
    df, yearly_data = load_data()

    # -------------------------
    # 원본 데이터 요약통계
    # -------------------------
    st.subheader("원본 데이터 요약통계")

    numeric_columns = ["평균기온", "최저기온", "최고기온"]

    summary = df[numeric_columns].describe().T

    summary = summary.rename(
        columns={
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

    summary.index = ["평균기온", "최저기온", "최고기온"]

    st.dataframe(
        summary.round(2),
        use_container_width=True
    )

    # -------------------------
    # 연도별 데이터 이상 여부 확인
    # -------------------------
    st.subheader("연도별 연평균 기온 변화")

    # 데이터에 존재하는 가장 이른 연도 ~ 가장 늦은 연도
    min_year = int(df["연도"].min())
    max_year = int(df["연도"].max())

    # 모든 연도를 생성해서 데이터가 없는 연도도 찾음
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

    # 전체 연평균과 표준편차
    overall_mean = yearly_data["연평균기온"].mean()
    overall_std = yearly_data["연평균기온"].std()

    # 유난히 낮은 연도 기준
    low_threshold = overall_mean - (2 * overall_std)

    yearly_data["상태"] = "정상"

    # 값이 없는 연도
    yearly_data.loc[
        yearly_data["연평균기온"].isna(),
        "상태"
    ] = "데이터 없음"

    # 평균보다 2표준편차 이상 낮은 연도
    yearly_data.loc[
        yearly_data["연평균기온"] < low_threshold,
        "상태"
    ] = "유난히 낮음"

    # -------------------------
    # 그래프
    # -------------------------
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
    line = base.mark_line(
        point=False
    )

    # 일반 데이터 점
    normal_points = (
        base.transform_filter(
            alt.datum.상태 == "정상"
        )
        .mark_circle(size=35)
    )

    # 이상 데이터 점
    abnormal_points = (
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
                legend=alt.Legend(title="이상 여부")
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
        (line + normal_points + abnormal_points)
        .properties(height=500)
    )

    st.altair_chart(
        chart,
        use_container_width=True
    )

    st.caption(
        "빨간색은 해당 연도의 기온 데이터가 없는 경우, "
        "주황색은 전체 연평균 기온보다 2표준편차 이상 낮은 경우입니다."
    )

    # -------------------------
    # 이상 연도 목록
    # -------------------------
    abnormal = yearly_data[
        yearly_data["상태"] != "정상"
    ][["연도", "연평균기온", "상태"]].copy()

    if len(abnormal) > 0:
        st.subheader("확인이 필요한 연도")

        abnormal["연평균기온"] = abnormal["연평균기온"].round(2)

        st.dataframe(
            abnormal,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.success("확인 기준에 해당하는 이상 연도가 없습니다.")

    # -------------------------
    # 데이터 기본 정보
    # -------------------------
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

except Exception as e:
    st.error("데이터를 불러오는 중 오류가 발생했습니다.")
    st.write(e)
