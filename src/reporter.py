"""HTML 리포트 렌더링 모듈."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


TEMPLATE_NAME = "report_template.html"


def render_html_report(
    charts: dict,
    quality_df: pd.DataFrame,
    meta: dict,
    output_path: str,
) -> None:
    """차트/품질요약/메타정보를 HTML 리포트로 렌더링한다."""
    project_root = Path(__file__).resolve().parent.parent
    template_dir = project_root / "templates"

    if not template_dir.exists():
        raise ValueError(f"템플릿 폴더를 찾을 수 없습니다: {template_dir}")

    env = Environment(
        loader=FileSystemLoader(str(template_dir)),
        autoescape=select_autoescape(["html", "xml"]),
    )

    try:
        template = env.get_template(TEMPLATE_NAME)
    except Exception as exc:
        raise ValueError(f"리포트 템플릿 로드에 실패했습니다: {exc}") from exc

    chart_html_map: dict[str, str] = {}
    for title, fig in charts.items():
        try:
            chart_html_map[title] = fig.to_html(full_html=False, include_plotlyjs=False)
        except Exception as exc:
            raise ValueError(f"차트 HTML 변환에 실패했습니다: {title} ({exc})") from exc

    quality_rows = quality_df.to_dict(orient="records")

    try:
        rendered_html = template.render(
            charts=chart_html_map,
            quality_rows=quality_rows,
            meta=meta,
        )
    except Exception as exc:
        raise ValueError(f"리포트 렌더링 중 오류가 발생했습니다: {exc}") from exc

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        out_path.write_text(rendered_html, encoding="utf-8")
    except Exception as exc:
        raise ValueError(
            f"리포트 파일 저장에 실패했습니다: {out_path} ({exc})"
        ) from exc
