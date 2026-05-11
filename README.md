# OceanQC

해양 관측 데이터 품질 자동 진단을 위한 **Python CLI 포트폴리오 프로젝트**입니다.

-   프로젝트명: OceanQC
-   한 줄 설명: 관측소별 결측률·이상치율·데이터 가용률을 진단하고 HTML 리포트로 생성하는 도구
-   핵심 스택: `pandas`, `plotly`, `jinja2`, `argparse`, `pytest`

## 현재 진행 상태

현재는 **초기 구조 + 샘플 데이터 생성기**까지 구현된 상태입니다.

구현 완료:

-   `config.py`
-   `data/generate_sample.py`
-   `requirements.txt`
-   `.gitignore`

예정:

-   `src/` 데이터 로딩/전처리/품질진단 모듈
-   Plotly 시각화
-   Jinja2 HTML 리포트 렌더링
-   `main.py` CLI 실행
-   `tests/` 단위 테스트

## 실행 환경

-   Python 3.11+

## 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 샘플 데이터 생성

```bash
python data/generate_sample.py
```

생성 결과:

-   `data/sample.csv`
-   데이터 규모: 3개 관측소 × 90일 × 24시간 = 6,480행
-   결측치 약 8%, 이상치 약 2% 포함

## 목표 폴더 구조 (완성 기준)

```text
oceanqc/
├── main.py
├── config.py
├── requirements.txt
├── README.md
├── data/
│   ├── sample.csv
│   └── generate_sample.py
├── reports/
│   └── .gitkeep
├── templates/
│   └── report_template.html
├── src/
│   ├── __init__.py
│   ├── loader.py
│   ├── preprocessor.py
│   ├── quality_checker.py
│   ├── aggregator.py
│   ├── visualizer.py
│   └── reporter.py
└── tests/
    └── test_quality_checker.py
```

## 라이선스

개인 포트폴리오 용도로 작성 중입니다.