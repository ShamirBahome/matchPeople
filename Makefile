# Run from this directory: cd matchPeople && make run
VENV ?= venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask
PORT ?= 5050

.PHONY: help venv install run dev gunicorn clean clean-venv

help:
	@echo "make install  — venv + pip install"
	@echo "make run      — Flask dev server on port $(PORT)"
	@echo "make gunicorn — production WSGI"

venv:
	@test -d "$(VENV)" || python3 -m venv "$(VENV)"

install: venv
	$(PIP) install -U pip
	$(PIP) install -r requirements.txt

run dev: install
	$(FLASK) --app app run --debug --host 127.0.0.1 --port "$(PORT)"

gunicorn: install
	$(VENV)/bin/gunicorn -w 2 -b "127.0.0.1:$(PORT)" "app:app"

clean:
	rm -rf __pycache__ templates/__pycache__ 2>/dev/null || true

clean-venv:
	rm -rf "$(VENV)"
