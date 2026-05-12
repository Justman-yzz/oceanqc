"""시각화 모듈."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import DOMAIN_BOUNDS


GRADE_COLORS = {
    "A": "#639922",   # 초록
    "B": "#378ADD",   # 파랑
    "C": "#EF9F27",   # 주황
    "D": "#D85A30",   # 주황빨강
    "F": "#A32D2D",   # 빨강
}


def _require_columns(df: pd.DataFrame, required: list[str]) -> None:
    """필수 컬럼 존재 여부를 확인한다."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")


def chart_quality_grade(quality_df: pd.DataFrame) -> go.Figure:
    """관측소별 데이터 가용률 및 품질 등급 수평 막대 차트를 생성한다."""
    _require_columns(quality_df, ["station_name", "availability_rate", "grade"])

    plot_df = quality_df.sort_values("availability_rate", ascending=True).reset_index(drop=True)
    bar_colors = [GRADE_COLORS.get(g, "#8A8A8A") for g in plot_df["grade"]]

    fig = go.Figure(
        data=[
            go.Bar(
                x=plot_df["availability_rate"],
                y=plot_df["station_name"],
                orientation="h",
                marker={"color": bar_colors},
                text=plot_df["grade"],
                textposition="outside",
                hovertemplate=(
                    "관측소: %{y}<br>"
                    "가용률: %{x:.2f}%<br>"
                    "등급: %{text}<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="관측소별 데이터 가용률 및 품질 등급",
        xaxis_title="데이터 가용률(%)",
        yaxis_title="관측소",
        xaxis=dict(range=[0, 100]),
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig


def chart_missing_heatmap(df: pd.DataFrame) -> go.Figure:
    """날짜(행) × 관측소(열) 결측률 히트맵을 생성한다."""
    _require_columns(df, ["datetime", "station_name"])

    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("결측률 계산 대상 수치 컬럼이 없습니다.")

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date"])

    grouped = temp.groupby(["date", "station_name"], dropna=False)

    total_cells = grouped.size() * len(metric_cols)
    missing_cells = grouped[metric_cols].apply(lambda x: x.isna().sum().sum())
    missing_rate = (missing_cells / total_cells * 100).rename("missing_rate").reset_index()

    pivot = (
        missing_rate.pivot_table(
            index="date",
            columns="station_name",
            values="missing_rate",
            aggfunc="mean",
        )
        .fillna(0.0)
        .round(2)
    )

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=pivot.values,
                x=pivot.columns.tolist(),
                y=pivot.index.astype(str).tolist(),
                zmin=0,
                zmax=30,
                colorscale=[
                    [0.0, "#67B66B"],   # 초록 (0%)
                    [0.5, "#EF9F27"],   # 주황
                    [1.0, "#F3B5B5"],   # 연빨강 (30%+)
                ],
                colorbar={"title": "결측률(%)"},
                hovertemplate=(
                    "날짜: %{y}<br>"
                    "관측소: %{x}<br>"
                    "결측률: %{z:.2f}%<extra></extra>"
                ),
            )
        ]
    )

    fig.update_layout(
        title="날짜별 관측소 결측률 히트맵",
        xaxis_title="관측소",
        yaxis_title="날짜",
        template="plotly_white",
        margin=dict(l=80, r=30, t=60, b=50),
    )
    return fig
