"""OceanQC CLI 진입점."""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from src.loader import load_csv
from src.preprocessor import fill_missing
from src.quality_checker import build_quality_summary
from src.reporter import render_html_report
from src.visualizer import build_all_charts


def parse_args() -> argparse.Namespace:
    """CLI 인자를 파싱한다."""
    parser = argparse.ArgumentParser(
        description="해양 관측 데이터 품질을 자동 진단하고 HTML 리포트를 생성합니다."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="입력 CSV 파일 경로",
    )
    parser.add_argument(
        "-o",
        "--output",
        default="reports/",
        help="출력 폴더 경로 (기본값: reports/)",
    )
    parser.add_argument(
        "--fill",
        default="ffill",
        choices=["ffill", "linear", "none"],
        help="결측치 처리 전략 (기본값: ffill)",
    )
    parser.add_argument(
        "--grade-only",
        action="store_true",
        help="품질 등급 요약만 출력하고 종료합니다.",
    )
    return parser.parse_args()


def build_meta(df: pd.DataFrame, quality_df: pd.DataFrame) -> dict:
    """리포트 상단 요약 메타 정보를 생성한다."""
    if df.empty or "datetime" not in df.columns:
        date_range = "-"
    else:
        min_dt = pd.to_datetime(df["datetime"], errors="coerce").min()
        max_dt = pd.to_datetime(df["datetime"], errors="coerce").max()
        if pd.isna(min_dt) or pd.isna(max_dt):
            date_range = "-"
        else:
            date_range = f"{min_dt:%Y-%m-%d} ~ {max_dt:%Y-%m-%d}"

    if quality_df.empty:
        best_station = "-"
        best_grade = "-"
        avg_availability = 0.0
        alert_count = 0
    else:
        top_row = quality_df.iloc[0]
        best_station = str(top_row["station_name"])
        best_grade = str(top_row["grade"])
        avg_availability = round(float(quality_df["availability_rate"].mean()), 1)
        alert_count = int(quality_df["is_alert"].sum())

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "date_range": date_range,
        "station_count": int(df["station_name"].nunique()) if "station_name" in df.columns else 0,
        "avg_availability": avg_availability,
        "best_station": best_station,
        "best_grade": best_grade,
        "alert_count": alert_count,
    }


def print_grade_summary(quality_df: pd.DataFrame) -> None:
    """품질 등급 요약을 터미널에 출력한다."""
    cols = [
        "station_name",
        "total_records",
        "missing_rate",
        "outlier_rate",
        "availability_rate",
        "grade",
        "is_alert",
    ]
    print("\n📊 관측소별 품질 등급 요약")
    print(quality_df[cols].to_string(index=False))


def run() -> None:
    """OceanQC CLI 실행 함수."""
    args = parse_args()

    print("🚀 OceanQC 분석을 시작합니다.")
    print("📥 CSV 파일을 불러오는 중입니다...")
    df = load_csv(args.input)

    print(f"🧹 결측치 처리 전략 적용 중입니다... ({args.fill})")
    df_filled = fill_missing(df, strategy=args.fill)

    print("🧮 품질 요약 테이블을 계산하는 중입니다...")
    quality_df = build_quality_summary(df_filled)

    if args.grade_only:
        print_grade_summary(quality_df)
        print("\n✅ grade-only 모드로 실행이 완료되었습니다.")
        return

    print("📈 차트를 생성하는 중입니다...")
    charts = build_all_charts(df_filled, quality_df)

    output_dir = Path(args.output)
    report_path = output_dir / "oceanqc_report.html"
    summary_path = output_dir / "quality_summary.csv"

    print("📝 HTML 리포트를 생성하는 중입니다...")
    meta = build_meta(df_filled, quality_df)
    render_html_report(
        charts=charts,
        quality_df=quality_df,
        meta=meta,
        output_path=str(report_path),
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    quality_df.to_csv(summary_path, index=False, encoding="utf-8-sig")

    print("💾 결과 파일 저장이 완료되었습니다.")
    print(f" - 리포트: {report_path}")
    print(f" - 요약 CSV: {summary_path}")
    print("✅ OceanQC 분석이 완료되었습니다.")


if __name__ == "__main__":
    try:
        run()
    except ValueError as exc:
        print(f"❌ 입력/검증 오류: {exc}")
        raise SystemExit(1)
    except Exception as exc:
        print(f"❌ 실행 중 알 수 없는 오류가 발생했습니다: {exc}")
        raise SystemExit(1)
