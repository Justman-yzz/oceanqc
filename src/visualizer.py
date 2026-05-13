"""시각화 모듈."""

from __future__ import annotations

import numpy as np
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
    """월 선택형(버튼) 결측률 히트맵을 생성한다. x=일(1~31), y=관측소."""
    _require_columns(df, ["datetime", "station_name"])

    metric_cols = [col for col in DOMAIN_BOUNDS.keys() if col in df.columns]
    if not metric_cols:
        raise ValueError("결측률 계산 대상 수치 컬럼이 없습니다.")

    temp = df.copy()
    temp["dt"] = pd.to_datetime(temp["datetime"], errors="coerce")
    temp = temp.dropna(subset=["dt"])
    temp["date"] = temp["dt"].dt.date

    grouped = temp.groupby(["date", "station_name"], dropna=False)
    total_cells = grouped.size() * len(metric_cols)
    missing_cells = grouped[metric_cols].apply(lambda x: x.isna().sum().sum())
    missing_rate = (
        (missing_cells / total_cells * 100).rename("missing_rate").reset_index()
    )
    z_q95 = float(missing_rate["missing_rate"].quantile(0.95))
    zmax_value = float(np.ceil(max(30.0, z_q95) / 5.0) * 5.0)
    zmax_value = min(100.0, zmax_value)

    missing_rate["date"] = pd.to_datetime(missing_rate["date"], errors="coerce")
    missing_rate = missing_rate.dropna(subset=["date"])
    missing_rate["month_key"] = missing_rate["date"].dt.to_period("M").astype(str)
    missing_rate["month_num"] = missing_rate["date"].dt.month
    missing_rate["day"] = missing_rate["date"].dt.day

    month_keys = sorted(missing_rate["month_key"].unique().tolist())
    if not month_keys:
        raise ValueError("히트맵 생성을 위한 월별 데이터가 없습니다.")

    ordered_stations = _ordered_station_names(
        missing_rate["station_name"].dropna().unique().tolist()
    )
    y_labels = [_station_label(name) for name in ordered_stations]
    day_axis = list(range(1, 32))

    fig = go.Figure()
    buttons = []

    for idx, month_key in enumerate(month_keys):
        month_df = missing_rate[missing_rate["month_key"] == month_key]
        month_num = int(month_df["month_num"].iloc[0])
        month_label = f"{month_num}월"

        pivot = (
            month_df.pivot_table(
                index="station_name",
                columns="day",
                values="missing_rate",
                aggfunc="mean",
            )
            .reindex(index=ordered_stations, columns=day_axis)
            .round(2)
        )

        fig.add_trace(
            go.Heatmap(
                z=pivot.values.tolist(),
                x=day_axis,
                y=y_labels,
                visible=(idx == 0),
                zmin=0,
                zmax=zmax_value,
                xgap=2,
                ygap=2,
                colorscale=[
                    [0.0, "#DCE7D1"],   # 0%
                    [0.55, "#F0BF66"],  # 중간
                    [1.0, "#E8873A"],   # 30%+
                ],
                colorbar={
                    "title": {"text": "결측률(%)", "font": {"color": CHART_FONT_COLOR}},
                    "tickfont": {"color": CHART_TICK_COLOR},
                },
                meta=month_label,
                hovertemplate=(
                    "월: %{meta}<br>"
                    "일자: %{x}일<br>"
                    "관측소: %{y}<br>"
                    "결측률: %{z:.2f}%<extra></extra>"
                ),
            )
        )

        visible_mask = [False] * len(month_keys)
        visible_mask[idx] = True
        buttons.append(
            dict(
                label=month_label,
                method="update",
                args=[{"visible": visible_mask}],
            )
        )

    _apply_dark_layout(
        fig,
        title="",
        xaxis_title="일자",
        yaxis_title="관측소",
        show_xgrid=False,
        show_ygrid=False,
    )

    fig.update_xaxes(
        range=[0.5, 31.5],
        dtick=1,
    )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.0,
                y=1.0,
                xanchor="left",
                yanchor="bottom",
                pad={"t": 2, "r": 4},
                showactive=True,
                bgcolor="rgba(27, 32, 40, 0.85)",
                bordercolor=CHART_LINE_COLOR,
                borderwidth=1,
                font={"color": CHART_TICK_COLOR, "size": 12},
                buttons=buttons,
            )
        ]
    )

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
