.PHONY: run

run:
	python3 -m uvicorn app:app --reload --port 8787
