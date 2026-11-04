# One command end-to-end:   make all
PYTHON   ?= python3
DBT      ?= dbt
DBT_ARGS ?= --profiles-dir . --target dev

.PHONY: all install data build docs export charts azure-upload clean

all: data build export charts ## generate data -> dbt build -> Tableau extracts -> preview charts

install: ## install Python dependencies
	$(PYTHON) -m pip install -r requirements.txt

data: ## generate synthetic raw CSVs into data/raw (+ data/sample)
	$(PYTHON) scripts/generate_data.py

build: ## seeds, snapshots, models and all tests on DuckDB
	mkdir -p data/warehouse
	$(DBT) deps $(DBT_ARGS)
	$(DBT) build $(DBT_ARGS)

docs: ## dbt docs site with lineage graph (http://localhost:8080)
	$(DBT) docs generate $(DBT_ARGS)
	$(DBT) docs serve $(DBT_ARGS)

export: ## export marts to tableau/data/*.csv
	$(PYTHON) scripts/export_for_tableau.py

charts: ## render preview PNGs into docs/images
	$(PYTHON) scripts/make_charts.py

azure-upload: ## upload data/raw to Azure Blob / ADLS (needs AZURE_STORAGE_CONNECTION_STRING)
	$(PYTHON) scripts/load_to_azure_blob.py

clean:
	rm -rf target logs dbt_packages data/warehouse
