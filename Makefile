SHELL := /bin/bash
PYTHON ?= python

.PHONY: install install-dev fmt ci test sample

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

install-dev: install
	$(PYTHON) -m pip install -r requirements-dev.txt

fmt:
	black .

ci:
	black --check .
	$(PYTHON) -m py_compile config.py data/generate_sample.py
	@if [ -d tests ] && ls tests/test_*.py >/dev/null 2>&1; then \
		pytest -q; \
	else \
		echo "테스트 파일이 없어 test 단계는 건너뜁니다."; \
	fi

test:
	pytest -q

sample:
	$(PYTHON) data/generate_sample.py
