# Installation

## Python

Python 3.11+ is required.

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest -q
```

## Run the offline demo

```bash
python scripts/run_pipeline.py
streamlit run dashboard/app.py
```

The offline demo uses deterministic synthetic market/credit data and a local SQLite database.

## PostgreSQL mode

Create a PostgreSQL database, apply `sql/schema.sql` if you want to inspect the reference DDL directly, then set:

```bash
export RISKQUANT_DATABASE_URL='postgresql+psycopg2://user:password@host:5432/riskquant'
python scripts/run_pipeline.py
```

The Python repository can create the required tables through SQLAlchemy as well. Never commit credentials.
