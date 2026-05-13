"""시각화 모듈."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from config import DOMAIN_BOUNDS, STATION_COLORS
from src.preprocessor import detect_all_outliers


GRADE_COLORS = {
    "A": "#639922",  # 초록
    "B": "#378ADD",  # 파랑
    "C": "#EF9F27",  # 주황
    "D": "#D85A30",  # 주황빨강
    "F": "#A32D2D",  # 빨강
}

STATION_SHORT_NAMES = {
    "모의 관측소 A": "obs-A",
    "모의 관측소 B": "obs-B",
    "모의 관측소 C": "obs-C",
    "모의 관측소 D": "obs-D",
    "모의 관측소 E": "obs-E",
    "모의 관측소 F": "obs-F",
    "모의 관측소 G": "obs-G",
    "모의 관측소 H": "obs-H",
    "모의 관측소 I": "obs-I",
    "모의 관측소 J": "obs-J",
}

CHART_FONT_COLOR = "#E6EDF5"
CHART_TICK_COLOR = "#C7D2E4"
CHART_GRID_COLOR = "rgba(170, 188, 212, 0.18)"
CHART_LINE_COLOR = "rgba(170, 188, 212, 0.35)"
CHART_ZERO_COLOR = "rgba(170, 188, 212, 0.26)"
CHART_BG_COLOR = "rgba(0, 0, 0, 0)"


def _require_columns(df: pd.DataFrame, required: list[str]) -> None:
    """필수 컬럼 존재 여부를 확인한다."""
    missing = [col for col in required if col not in df.columns]
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")


def _ordered_station_names(station_names: list[str]) -> list[str]:
    """관측소 이름을 STATION_COLORS 기준 순서로 정렬한다."""
    base_order = [name for name in STATION_COLORS.keys() if name in station_names]
    others = [name for name in station_names if name not in base_order]
    return base_order + sorted(others)


def _station_color(station_name: str) -> str:
    """관측소별 고정 색상을 반환한다."""
    return STATION_COLORS.get(station_name, "#8A8A8A")


def _station_label(station_name: str) -> str:
    """차트 범례/축용 축약 관측소명을 반환한다."""
    return STATION_SHORT_NAMES.get(station_name, station_name)


def _apply_dark_layout(
    fig: go.Figure,
    *,
    title: str,
    xaxis_title: str,
    yaxis_title: str,
    show_xgrid: bool = True,
    show_ygrid: bool = True,
) -> None:
    """공통 다크 테마 레이아웃을 적용한다."""
    fig.update_layout(
        title={
            "text": title,
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 22, "color": CHART_FONT_COLOR},
        },
        font={"color": CHART_FONT_COLOR},
        paper_bgcolor=CHART_BG_COLOR,
        plot_bgcolor=CHART_BG_COLOR,
        margin={"l": 80, "r": 30, "t": 60, "b": 50},
        legend={
            "bgcolor": "rgba(0,0,0,0)",
            "font": {"color": CHART_TICK_COLOR, "size": 13},
        },
    )

    fig.update_xaxes(
        title_text=xaxis_title,
        title_font={"color": CHART_FONT_COLOR},
        tickfont={"color": CHART_TICK_COLOR},
        showgrid=show_xgrid,
        gridcolor=CHART_GRID_COLOR,
        gridwidth=1,
        showline=True,
        linecolor=CHART_LINE_COLOR,
        zeroline=True,
        zerolinecolor=CHART_ZERO_COLOR,
    )
    fig.update_yaxes(
        title_text=yaxis_title,
        title_font={"color": CHART_FONT_COLOR},
        tickfont={"color": CHART_TICK_COLOR},
        showgrid=show_ygrid,
        gridcolor=CHART_GRID_COLOR,
        gridwidth=1,
        showline=True,
        linecolor=CHART_LINE_COLOR,
        zeroline=True,
        zerolinecolor=CHART_ZERO_COLOR,
    )


def chart_quality_grade(quality_df: pd.DataFrame) -> go.Figure:
    """관측소별 데이터 가용률 및 품질 등급 수평 막대 차트를 생성한다."""
    _require_columns(quality_df, ["station_name", "availability_rate", "grade"])

    plot_df = quality_df.sort_values("availability_rate", ascending=True).reset_index(
        drop=True
    )
    plot_df["station_label"] = plot_df["station_name"].apply(_station_label)
    bar_colors = [GRADE_COLORS.get(g, "#8A8A8A") for g in plot_df["grade"]]

    bar_x = plot_df["availability_rate"].round(2).tolist()
    bar_y = plot_df["station_label"].tolist()
    bar_text = [f"{v:.1f}%" for v in bar_x]
    bar_customdata = list(
        zip(
            plot_df["station_name"].tolist(),
            plot_df["grade"].tolist(),
            bar_x,
        )
    )

    fig = go.Figure(
        data=[
            go.Bar(
                x=bar_x,
                y=bar_y,
                orientation="h",
                marker={"color": bar_colors},
                customdata=bar_customdata,
                text=bar_text,
                textposition="outside",
                hovertemplate=(
                    "관측소: %{customdata[0]}<br>"
                    "가용률: %{customdata[2]:.2f}%<br>"
                    "등급: %{customdata[1]}<extra></extra>"
                ),
            )
        ]
    )

    _apply_dark_layout(
        fig,
        title="관측소별 데이터 가용률 및 품질 등급",
        xaxis_title="데이터 가용률(%)",
        yaxis_title="관측소",
    )
    fig.update_xaxes(range=[0, 100])
    fig.update_yaxes(
        categoryorder="array",
        categoryarray=bar_y,
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
    missing_rate = (
        (missing_cells / total_cells * 100).rename("missing_rate").reset_index()
    )

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

    ordered_cols = _ordered_station_names(pivot.columns.tolist())
    pivot = pivot.reindex(columns=ordered_cols)

    fig = go.Figure(
        data=[
            go.Heatmap(
                z=pivot.values,
                x=[_station_label(col) for col in pivot.columns.tolist()],
                y=pivot.index.astype(str).tolist(),
                zmin=0,
                zmax=30,
                colorscale=[
                    [0.0, "#DCE7D1"],  # 0%
                    [0.55, "#F0BF66"],  # 중간
                    [1.0, "#E8873A"],  # 30%+
                ],
                colorbar={
                    "title": {"text": "결측률(%)", "font": {"color": CHART_FONT_COLOR}},
                    "tickfont": {"color": CHART_TICK_COLOR},
                },
                hovertemplate=(
                    "날짜: %{y}<br>"
                    "관측소: %{x}<br>"
                    "결측률: %{z:.2f}%<extra></extra>"
                ),
            )
        ]
    )

    _apply_dark_layout(
        fig,
        title="날짜별 관측소 결측률 히트맵",
        xaxis_title="관측소",
        yaxis_title="날짜",
        show_xgrid=False,
        show_ygrid=False,
    )
    fig.update_yaxes(nticks=10)

    return fig


def chart_daily_wind_speed(df: pd.DataFrame) -> go.Figure:
    """일별 평균 풍속 라인 차트를 생성한다."""
    _require_columns(df, ["datetime", "station_name", "wind_speed"])

    temp = df.copy()
    temp["date"] = pd.to_datetime(temp["datetime"], errors="coerce").dt.date
    temp = temp.dropna(subset=["date", "wind_speed"])

    daily = (
        temp.groupby(["date", "station_name"], dropna=False)["wind_speed"]
        .mean()
        .reset_index()
    )

    ordered_stations = _ordered_station_names(
        daily["station_name"].dropna().unique().tolist()
    )

    fig = go.Figure()
    for station_name in ordered_stations:
        station_df = daily[daily["station_name"] == station_name]
        if station_df.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=station_df["date"],
                y=station_df["wind_speed"],
                mode="lines",
                name=_station_label(station_name),
                line=dict(color=_station_color(station_name), width=2.4),
                hovertemplate=(
                    "날짜: %{x}<br>"
                    "관측소: %{fullData.name}<br>"
                    "평균 풍속: %{y:.2f} m/s<extra></extra>"
                ),
            )
        )

    _apply_dark_layout(
        fig,
        title="일별 평균 풍속 추이 (관측소별)",
        xaxis_title="날짜",
        yaxis_title="풍속(m/s)",
    )

    return fig


def chart_wind_wave_scatter(df: pd.DataFrame) -> go.Figure:
    """풍속(x) × 파고(y) 산점도를 생성한다."""
    _require_columns(df, ["station_name", "wind_speed", "wave_height"])

    outlier_mask = detect_all_outliers(df)
    pair_outlier = outlier_mask[["wind_speed", "wave_height"]].any(axis=1)

    temp = df.copy()
    temp["is_outlier"] = pair_outlier
    plot_df = temp.dropna(subset=["wind_speed", "wave_height"])

    normal_df = plot_df[~plot_df["is_outlier"]]
    outlier_df = plot_df[plot_df["is_outlier"]]

    fig = go.Figure()

    ordered_stations = _ordered_station_names(
        normal_df["station_name"].dropna().unique().tolist()
    )
    for station_name in ordered_stations:
        station_df = normal_df[normal_df["station_name"] == station_name]
        if station_df.empty:
            continue

        fig.add_trace(
            go.Scatter(
                x=station_df["wind_speed"],
                y=station_df["wave_height"],
                mode="markers",
                name=_station_label(station_name),
                marker=dict(
                    size=6.5,
                    opacity=0.82,
                    color=_station_color(station_name),
                    line=dict(color="rgba(0,0,0,0.45)", width=0.5),
                ),
                hovertemplate=(
                    "관측소: %{fullData.name}<br>"
                    "풍속: %{x:.2f} m/s<br>"
                    "파고: %{y:.2f} m<extra></extra>"
                ),
            )
        )

    if not outlier_df.empty:
        fig.add_trace(
            go.Scatter(
                x=outlier_df["wind_speed"],
                y=outlier_df["wave_height"],
                mode="markers",
                name="이상치",
                marker=dict(
                    size=8.5,
                    color="#EF9F27",
                    line=dict(color="#854F0B", width=1.6),
                    symbol="diamond",
                ),
                hovertemplate=(
                    "구분: 이상치<br>"
                    "풍속: %{x:.2f} m/s<br>"
                    "파고: %{y:.2f} m<extra></extra>"
                ),
            )
        )

    _apply_dark_layout(
        fig,
        title="풍속 × 파고 상관관계",
        xaxis_title="풍속(m/s)",
        yaxis_title="파고(m)",
    )

    return fig


def build_all_charts(
    df: pd.DataFrame, quality_df: pd.DataFrame
) -> dict[str, go.Figure]:
    """리포트 출력 순서대로 차트 4개를 묶어 반환한다."""
    return {
        "관측소별 데이터 가용률 및 품질 등급": chart_quality_grade(quality_df),
        "날짜별 관측소 결측률 히트맵": chart_missing_heatmap(df),
        "일별 평균 풍속 추이 (관측소별)": chart_daily_wind_speed(df),
        "풍속 × 파고 상관관계": chart_wind_wave_scatter(df),
    }
