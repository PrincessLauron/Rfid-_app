.PHONY: web test

web:
	./start_webapp.sh

test:
	. .venv/bin/activate && python -m unittest discover -s tests -q
