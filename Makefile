PY?=python
TMPDIR?=/tmp

.PHONY: install install-dev fmt lint type test check

install:
	$(PY) -m pip install -r requirements.txt

install-dev: install
	$(PY) -m pip install -r requirements-dev.txt

fmt:
	$(PY) -m black gateway tests

lint:
	$(PY) -m ruff check gateway tests

type:
	$(PY) -m mypy gateway

test:
	TMPDIR=$(TMPDIR) $(PY) -m pytest

check: fmt lint type test

.PHONY: openapi
openapi:
	$(PY) scripts/export_openapi.py

.PHONY: grpc
grpc:
	$(PY) -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. artifacts/api/homegateway.proto
