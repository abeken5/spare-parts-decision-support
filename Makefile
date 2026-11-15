.PHONY: setup pipeline test demo

setup:
	pip install -r requirements.txt

pipeline:
	python data/generator.py
	python src/ingestion/load_sqlite.py
	python src/segmentation/classify.py
	python src/forecasting/compete.py
	python src/inventory/classical.py
	python src/simulation/bootstrap.py
	python src/evaluation/backtest.py
	python src/reporting/action_plan.py

test:
	pytest

demo: pipeline
	streamlit run app/streamlit_app.py
