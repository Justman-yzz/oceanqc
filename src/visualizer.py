"""시각화 모듈."""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from config import DOMAIN_BOUNDS, STATION_COLORS, WIND_LINE_GAP_THRESHOLDS
from src.preprocessor import detect_outliers_domain, detect_outliers_iqr


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
        title="",  # 카드 제목만 사용
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
    """전체/월 선택형 일별 평균 풍속 라인 차트를 생성한다."""
    _require_columns(df, ["datetime", "station_name", "wind_speed"])

    safe_max = WIND_LINE_GAP_THRESHOLDS["safe_max_missing_ratio"]
    warn_max = WIND_LINE_GAP_THRESHOLDS["warn_max_missing_ratio"]
    if not (0.0 <= safe_max < warn_max <= 1.0):
        raise ValueError(
            "WIND_LINE_GAP_THRESHOLDS 설정이 올바르지 않습니다. "
            "(0 <= safe < warn <= 1 이어야 합니다.)"
        )

    temp = df.copy()
    temp["dt"] = pd.to_datetime(temp["datetime"], errors="coerce")
    temp = temp.dropna(subset=["dt"])
    temp["date"] = temp["dt"].dt.date
    temp["month_num"] = temp["dt"].dt.month
    temp["day"] = temp["dt"].dt.day

    daily = (
        temp.groupby(["date", "month_num", "day", "station_name"], dropna=False)
        .agg(
            wind_speed_mean=("wind_speed", "mean"),
            wind_obs_count=("wind_speed", "count"),
            day_row_count=("wind_speed", "size"),
        )
        .reset_index()
    )
    daily["date"] = pd.to_datetime(daily["date"], errors="coerce")
    daily = daily.dropna(subset=["date"])

    if daily.empty:
        raise ValueError("풍속 추이 차트를 생성할 데이터가 없습니다.")

    daily["missing_ratio"] = np.where(
        daily["day_row_count"] > 0,
        1.0 - (daily["wind_obs_count"] / daily["day_row_count"]),
        1.0,
    )
    daily["gap_level"] = np.select(
        [
            daily["missing_ratio"] < safe_max,
            daily["missing_ratio"] < warn_max,
        ],
        ["safe", "warn"],
        default="severe",
    )

    ordered_stations = _ordered_station_names(
        daily["station_name"].dropna().unique().tolist()
    )
    month_nums = sorted(int(m) for m in daily["month_num"].dropna().unique().tolist())
    scope_defs = [("전체", "all", None)] + [(f"{m}월", f"m{m}", m) for m in month_nums]

    fig = go.Figure()
    trace_scope_keys: list[str] = []

    for scope_label, scope_key, scope_month in scope_defs:
        scope_df = daily if scope_month is None else daily[daily["month_num"] == scope_month]

        for station_name in ordered_stations:
            station_df = (
                scope_df[scope_df["station_name"] == station_name]
                .sort_values("date")
                .reset_index(drop=True)
            )
            if station_df.empty:
                continue

            color = _station_color(station_name)
            station_label = _station_label(station_name)
            is_default_scope = scope_month is None

            if scope_month is None:
                x_vals = station_df["date"].tolist()
                hover_head = "날짜: %{x|%Y-%m-%d}<br>"
            else:
                x_vals = station_df["day"].tolist()
                hover_head = f"월: {scope_label}<br>일자: %{{x}}일<br>"

            y_vals = [
                None if pd.isna(v) else float(v)
                for v in station_df["wind_speed_mean"].tolist()
            ]
            level_mask = station_df["gap_level"].tolist()

            # safe: 실선, warn: 점선, severe: 선 끊김(None)
            y_solid = [y if lv == "safe" else None for y, lv in zip(y_vals, level_mask)]
            y_dash = [y if lv == "warn" else None for y, lv in zip(y_vals, level_mask)]

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_solid,
                    mode="lines+markers",
                    name=station_label,
                    legendgroup=station_name,
                    showlegend=True,
                    visible=is_default_scope,
                    connectgaps=False,
                    line=dict(color=color, width=2.2, dash="solid"),
                    marker=dict(size=4.2, color=color),
                    hovertemplate=(
                        hover_head
                        + "관측소: %{fullData.name}<br>"
                        + "평균 풍속: %{y:.2f} m/s<extra></extra>"
                    ),
                )
            )
            trace_scope_keys.append(scope_key)

            fig.add_trace(
                go.Scatter(
                    x=x_vals,
                    y=y_dash,
                    mode="lines+markers",
                    name=f"{station_label} 결측주의",
                    legendgroup=station_name,
                    showlegend=False,
                    visible=is_default_scope,
                    connectgaps=False,
                    line=dict(color=color, width=2.2, dash="dot"),
                    marker=dict(size=3.2, color=color, opacity=0.9),
                    hovertemplate=(
                        hover_head
                        + f"관측소: {station_label}<br>"
                        + "구간: 결측 주의(점선)<br>"
                        + "평균 풍속: %{y:.2f} m/s<extra></extra>"
                    ),
                )
            )
            trace_scope_keys.append(scope_key)

    _apply_dark_layout(
        fig,
        title="",
        xaxis_title="날짜",
        yaxis_title="풍속(m/s)",
    )

    valid_ws = daily["wind_speed_mean"].dropna()
    y_max = float(valid_ws.max()) if not valid_ws.empty else 1.0
    y_upper = max(1.0, round(y_max * 1.12, 1))
    fig.update_yaxes(range=[0, y_upper])

    fig.update_layout(
        height=680,
        margin=dict(t=210),
        legend=dict(
            orientation="h",
            x=0.0,
            y=1.32,
            xanchor="left",
            yanchor="bottom",
            traceorder="normal",
            groupclick="togglegroup",
            font={"color": CHART_TICK_COLOR, "size": 11},
        ),
        uirevision="wind-month-toggle",
    )

    buttons = []
    for scope_label, scope_key, scope_month in scope_defs:
        visible_mask = [k == scope_key for k in trace_scope_keys]

        if scope_month is None:
            xaxis_update = {
                "type": "date",
                "title": {"text": "날짜", "font": {"color": CHART_FONT_COLOR}},
                "tickformat": "%m-%d",
                "dtick": "M1",
                "showgrid": True,
                "gridcolor": CHART_GRID_COLOR,
                "gridwidth": 1,
            }
            shapes_update = []
        else:
            week_lines = [1, 8, 15, 22, 29]
            week_labels_x = [4.5, 11.5, 18.5, 25.5]

            xaxis_update = {
                "type": "linear",
                "title": {"text": "주차", "font": {"color": CHART_FONT_COLOR}},
                "range": [0.5, 31.5],
                "tickmode": "array",
                "tickvals": week_labels_x,
                "ticktext": ["1주", "2주", "3주", "4주"],
                "showgrid": False,
                "zeroline": False,
            }

            shapes_update = [
                {
                    "type": "line",
                    "xref": "x",
                    "yref": "paper",
                    "x0": x,
                    "x1": x,
                    "y0": 0,
                    "y1": 1,
                    "line": {"color": "rgba(255, 255, 255, 0.42)", "width": 1.6},
                    "layer": "below",
                }
                for x in week_lines
            ]

        buttons.append(
            dict(
                label=scope_label,
                method="update",
                args=[
                    {"visible": visible_mask},
                    {"xaxis": xaxis_update, "shapes": shapes_update},
                ],
            )
        )

    fig.update_layout(
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.0,
                y=1.10,
                xanchor="left",
                yanchor="bottom",
                showactive=True,
                pad={"t": 2, "r": 4},
                bgcolor="rgba(27, 32, 40, 0.85)",
                bordercolor=CHART_LINE_COLOR,
                borderwidth=1,
                font={"color": CHART_TICK_COLOR, "size": 12},
                buttons=buttons,
            )
        ]
    )

    return fig


def chart_wind_wave_scatter(df: pd.DataFrame) -> go.Figure:
    """풍속-파고 관계 기반 이상치 확인 산점도를 생성한다."""
    _require_columns(df, ["station_name", "wind_speed", "wave_height"])

    temp = df.copy()
    temp = temp.dropna(subset=["wind_speed", "wave_height"]).reset_index(drop=True)
    if temp.empty:
        raise ValueError("산점도를 생성할 풍속/파고 데이터가 없습니다.")

    # 1) 도메인/통계 이상치 후보 계산
    domain_mask_df = detect_outliers_domain(temp)
    iqr_mask_df = detect_outliers_iqr(temp)
    temp["is_domain_outlier"] = domain_mask_df[["wind_speed", "wave_height"]].any(axis=1)
    temp["is_iqr_outlier"] = iqr_mask_df[["wind_speed", "wave_height"]].any(axis=1)

    # 2) 교차검증용 기준선(정상 후보만) 계산
    baseline_df = temp[~temp["is_domain_outlier"] & ~temp["is_iqr_outlier"]].copy()
    model_ready = (
        len(baseline_df) >= 20
        and float(baseline_df["wind_speed"].std(ddof=0)) > 0.0
        and float(baseline_df["wave_height"].std(ddof=0)) > 0.0
    )

    temp["is_residual_outlier"] = False
    corr_value = None
    residual_cut = 0.25

    if model_ready:
        bx = baseline_df["wind_speed"].to_numpy(dtype=float)
        by = baseline_df["wave_height"].to_numpy(dtype=float)
        slope, intercept = np.polyfit(bx, by, 1)

        base_pred = slope * bx + intercept
        base_residual = np.abs(by - base_pred)

        # 정상 후보 residual 상위 0.5% 기준으로 교차검증 임계값 설정
        residual_cut = float(np.quantile(base_residual, 0.995))
        residual_cut = max(residual_cut, 0.25)

        all_x = temp["wind_speed"].to_numpy(dtype=float)
        all_y = temp["wave_height"].to_numpy(dtype=float)
        all_pred = slope * all_x + intercept
        all_residual = np.abs(all_y - all_pred)
        temp["is_residual_outlier"] = all_residual > residual_cut

        # Pearson은 정상 구간에서만 계산
        if len(baseline_df) >= 2:
            corr_value = float(np.corrcoef(bx, by)[0, 1])

    # 3) 최종 이상치: 도메인 OR (IQR AND 교차검증 통과)
    if model_ready:
        temp["is_outlier_final"] = temp["is_domain_outlier"] | (
            temp["is_iqr_outlier"] & temp["is_residual_outlier"]
        )
    else:
        # 모델 계산 불가 시 보수적 fallback
        temp["is_outlier_final"] = temp["is_domain_outlier"] | temp["is_iqr_outlier"]

    normal_df = temp[~temp["is_outlier_final"]].copy()
    outlier_df = temp[temp["is_outlier_final"]].copy()

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
                    size=6.0,
                    opacity=0.30,
                    color=_station_color(station_name),
                    line=dict(color="rgba(0,0,0,0.25)", width=0.4),
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
                name="최종 이상치",
                marker=dict(
                    size=8.8,
                    color="#EF9F27",
                    opacity=0.95,
                    symbol="diamond",
                    line=dict(color="#854F0B", width=1.8),
                ),
                hovertemplate=(
                    "구분: 최종 이상치<br>"
                    "풍속: %{x:.2f} m/s<br>"
                    "파고: %{y:.2f} m<extra></extra>"
                ),
            )
        )

    # 정상 구간 추세선(옵션 B: 정상 데이터 기준)
    show_trend = (
        len(normal_df) >= 20
        and float(normal_df["wind_speed"].std(ddof=0)) > 0.0
        and float(normal_df["wave_height"].std(ddof=0)) > 0.0
    )
    if show_trend:
        nx = normal_df["wind_speed"].to_numpy(dtype=float)
        ny = normal_df["wave_height"].to_numpy(dtype=float)
        slope_n, intercept_n = np.polyfit(nx, ny, 1)
        x_line = np.linspace(float(np.min(nx)), float(np.max(nx)), 120)
        y_line = slope_n * x_line + intercept_n

        fig.add_trace(
            go.Scatter(
                x=x_line,
                y=y_line,
                mode="lines",
                name="정상구간 추세선",
                line=dict(color="rgba(245,245,245,0.78)", width=1.6, dash="dash"),
                hovertemplate=(
                    "정상구간 추세선<br>"
                    "y = {:.3f}x + {:.3f}<extra></extra>"
                ).format(slope_n, intercept_n),
            )
        )

    def _range_with_padding(values: pd.Series, fallback: tuple[float, float]) -> list[float]:
        """하위 1% ~ 상위 99% 구간을 기준으로 축 범위를 계산한다."""
        arr = values.dropna().to_numpy(dtype=float)
        if arr.size == 0:
            return [fallback[0], fallback[1]]
        lo = float(np.quantile(arr, 0.01))
        hi = float(np.quantile(arr, 0.99))
        if hi <= lo:
            lo = float(np.min(arr))
            hi = float(np.max(arr))
        span = max(hi - lo, 1.0)
        pad = span * 0.10
        return [lo - pad, hi + pad]

    x_zoom = _range_with_padding(normal_df["wind_speed"], DOMAIN_BOUNDS["wind_speed"])
    y_zoom = _range_with_padding(normal_df["wave_height"], DOMAIN_BOUNDS["wave_height"])
    x_full = _range_with_padding(temp["wind_speed"], DOMAIN_BOUNDS["wind_speed"])
    y_full = _range_with_padding(temp["wave_height"], DOMAIN_BOUNDS["wave_height"])

    _apply_dark_layout(
        fig,
        title="",  # 카드 제목만 사용
        xaxis_title="풍속(m/s)",
        yaxis_title="파고(m)",
    )
    fig.update_xaxes(range=x_zoom)
    fig.update_yaxes(range=y_zoom)

    total_n = len(temp)
    outlier_n = int(outlier_df.shape[0])
    outlier_ratio = (outlier_n / total_n * 100.0) if total_n > 0 else 0.0

    corr_label = "정상구간 Pearson r: 계산불가"
    if corr_value is not None:
        corr_label = (
            f"정상구간 Pearson r: {corr_value:.2f}"
            if abs(corr_value) >= 0.15
            else "정상구간 Pearson r: 약한 상관"
        )

    summary_text = (
        f"최종 이상치 {outlier_n:,}건 / 전체 {total_n:,}건 ({outlier_ratio:.2f}%) · {corr_label}"
    )

    fig.update_layout(
        height=680,
        legend=dict(
            orientation="h",
            x=0.0,
            y=1.24,
            xanchor="left",
            yanchor="bottom",
            entrywidth=74,
            font={"color": CHART_TICK_COLOR, "size": 10},
        ),
        margin=dict(t=188, b=170),
        annotations=[
            dict(
                x=0.0,
                y=-0.30,
                xref="paper",
                yref="paper",
                xanchor="left",
                yanchor="top",
                showarrow=False,
                text=summary_text,
                font={"size": 12, "color": "#AEB9CB"},
                bgcolor="rgba(15, 20, 30, 0.72)",
                bordercolor="rgba(170, 188, 212, 0.22)",
                borderwidth=1,
                borderpad=4,
            ),
        ],
        updatemenus=[
            dict(
                type="buttons",
                direction="right",
                x=0.0,
                y=1.02,
                xanchor="left",
                yanchor="bottom",
                showactive=True,
                pad={"t": 2, "r": 4},
                bgcolor="rgba(27, 32, 40, 0.85)",
                bordercolor=CHART_LINE_COLOR,
                borderwidth=1,
                font={"color": CHART_TICK_COLOR, "size": 12},
                buttons=[
                    dict(
                        label="정상 범위",
                        method="relayout",
                        args=[{"xaxis.range": x_zoom, "yaxis.range": y_zoom}],
                    ),
                    dict(
                        label="전체 범위",
                        method="relayout",
                        args=[{"xaxis.range": x_full, "yaxis.range": y_full}],
                    ),
                ],
            )
        ],
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
        "풍속-파고 관계 기반 이상치 확인": chart_wind_wave_scatter(df),
    }
