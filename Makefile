.PHONY: test help fmt lint run

VENV?=.venv
PIP=$(VENV)/bin/pip
PY=$(VENV)/bin/python
ORG?=xebia

help: ## list targets with short description
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z0-9._-]+:.*?## / {printf "\033[1m\033[36m%-38s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run: $(VENV)/requirements_init
	$(PY) ./gh-query.py members $(ORG) >members.ndjson
	$(PY) ./gh-query.py prs <members.ndjson >prs.ndjson

test: $(VENV)/requirements_init ## run pytest
	. $(VENV)/bin/activate && pytest -rA -vvs --log-level INFO

lint: $(VENV)/requirements_init ## run flake8 to check the code
	. $(VENV)/bin/activate && flake8 src tests *.py

fmt: $(VENV)/requirements_init ## run black to format the code
	. $(VENV)/bin/activate && black src tests *.py

$(VENV)/init: ## init the virtual environment
	python3 -m venv $(VENV)
	touch $@

$(VENV)/requirements_init: requirements.txt $(VENV)/init ## install requirements
	$(PIP) install -r $<
	touch $@
