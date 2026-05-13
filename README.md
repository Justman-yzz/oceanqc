# OceanQC

해양 관측 장비에서 수집되는 풍속·파고·수온·기압 데이터를 가정하고,  
관측소별 결측률·이상치율·데이터 가용률을 자동 진단해 HTML 리포트로 생성하는 Python CLI 도구입니다.

OceanQC는 해양 관측 데이터를 가정한 모의 CSV를 입력받아, 관측소별 결측률·이상치율·데이터 가용률을 계산하고 HTML 리포트로 자동 생성합니다.  
단순 시각화가 아니라, 관측 데이터가 **보고 가능한 품질인지 판단하고 그 기준을 설명 가능한 형태로 정리**하는 것을 목표로 했습니다.

> 본 프로젝트는 실제 관측 데이터가 아닌 모의 해양 관측 데이터를 사용한 개인 포트폴리오 프로젝트입니다.

## Links

-   GitHub Repository: [https://github.com/Justman-yzz/oceanqc](https://github.com/Justman-yzz/oceanqc)
-   Sample HTML Report (배포용): [https://justman-yzz.github.io/oceanqc/sample_report.html](https://justman-yzz.github.io/oceanqc/sample_report.html)
-   Sample HTML Report (저장소 파일): [docs/sample_report.html](docs/sample_report.html)

## 프로젝트 배경

실제 해양 관측 데이터는 통신 장애, 센서 오작동, 보정 오류 등으로 결측/이상치가 빈번히 발생합니다.  
이 프로젝트는 이런 품질 이슈를 관측소 단위로 자동 진단하고,  
“왜 이 관측소가 경보 대상인지”를 리포트에서 바로 확인할 수 있게 만드는 데 초점을 두었습니다.

## 주요 기능

-   CSV 입력 데이터 로드 및 필수 컬럼 검증
-   결측치 처리 전략 지원: `ffill`, `linear`, `none`
-   관측소별 품질 지표 계산
    -   결측률, 이상치율, 데이터 가용률, 등급(A~F), 경보 여부
-   Plotly 시각화 4종 자동 생성
    -   관측소별 가용률/등급
    -   월 선택형 결측률 히트맵
    -   전체/월 선택형 일별 평균 풍속 추이
    -   풍속-파고 관계 기반 이상치 확인
-   Jinja2 기반 단일 HTML 리포트 출력

## 실행 환경

-   Python `3.11+` (권장: `3.11`)

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python data/generate_sample.py
python main.py -i data/sample.csv -o reports/ --fill none
```

생성 결과:

-   `reports/oceanqc_report.html`
-   `reports/quality_summary.csv`

## CLI 실행 옵션

### 기본 실행

```bash
python main.py -i data/sample.csv -o reports/
```

-   기본 결측 전략은 `--fill ffill` 입니다.

### 품질 등급만 출력

```bash
python main.py -i data/sample.csv --grade-only
```

### 결측치 처리 전략 비교

```bash
python main.py -i data/sample.csv -o reports/ --fill none
python main.py -i data/sample.csv -o reports/ --fill ffill
python main.py -i data/sample.csv -o reports/ --fill linear
```

-   `none`: 원본 결측 패턴 유지(진단/비교 중심)
-   `ffill`: 직전값 보간(기본값)
-   `linear`: 선형 보간

포트폴리오 샘플 리포트는 **원본 결측 패턴을 보여주기 위해 `--fill none` 기준**으로 생성했습니다.

## 샘플 데이터

```bash
python data/generate_sample.py
```

-   생성 파일: `data/sample.csv`
-   데이터 규모: **10개 관측소 × 90일 × 24시간 = 21,600행**
-   관측소 명칭: `모의 관측소 01 ~ 10` / 차트 축약명 `obs-01 ~ obs-10`
-   관측소 티어별 결측/이상치 분포를 다르게 주입해 품질 차이를 재현

## 차트 해석 가이드

### 1) 관측소별 데이터 가용률 및 품질 등급

-   막대 길이 = 가용률(%)
-   등급 기준: `A ≥ 95`, `B ≥ 90`, `C ≥ 80`, `D ≥ 70`, `F < 70`

### 2) 날짜별 관측소 결측률 히트맵

-   월 버튼으로 `1~31일` 일자별 결측률 비교
-   진한 주황 구간은 결측률이 높은 구간(연속 시 통신/센서 이상 가능성)

### 3) 일별 평균 풍속 추이 (관측소별)

-   실선: 안정 구간(결측률 10% 미만)
-   점선: 결측 주의 구간(10~50%)
-   선 끊김: 결측 심화 구간(50% 이상)

### 4) 풍속-파고 관계 기반 이상치 확인

-   정상 분포 대비 크게 벗어나거나 도메인 임계값을 초과한 관측값을 이상치 후보로 표시
-   `정상 범위` / `전체 범위` 버튼으로 확대/전체 분포 비교 가능

## 인터랙티브 차트 안내

리포트는 Plotly CDN을 사용합니다.

```html
<script src="https://cdn.plot.ly/plotly-3.5.0.min.js"></script>
```

-   인터넷 연결 시: 인터랙티브 차트(확대/범례 토글/버튼) 정상 동작
-   오프라인 환경: 차트 영역이 비어 보일 수 있음

## 테스트/검증

```bash
make test
make ci
```

## 프로젝트 구조

```text
oceanqc/
├── main.py
├── config.py
├── requirements.txt
├── requirements-dev.txt
├── Makefile
├── README.md
├── data/
│   ├── generate_sample.py
│   └── sample.csv
├── docs/
│   └── sample_report.html
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

## License

본 프로젝트는 개인 포트폴리오 및 학습 목적으로 공개한 프로젝트입니다.