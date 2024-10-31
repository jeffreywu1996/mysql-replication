VENV := venv
REQS := requirements.txt

.PHONY: install
install:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -r $(REQS)

.PHONY: loadtest
loadtest:
	$(VENV)/bin/locust -f load_test.py --host=http://localhost
