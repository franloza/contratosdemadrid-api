#contratosdemadrid

## Getting started 

## 1. Install dependencies

- `pip install -r requirements.txt`

## 2. Start up database

- `docker-compose -d up`

### 3. Extract data

- `python3 src/etl/extract_csv.py --dir-path files/csv --start-date 2008-01-01`

### 4. Transform data

- `python3 src/etl/transform.py csv --input-dir-path files/json --output-dir-path files/json --start-date 2008-01-01`

### 5. Load (Requires step 1)

- `python3 src/etl/load.py companies --dir-path files/json --start-date 2008-01-01`
- `python3 src/etl/load.py contracts --dir-path files/json --start-date 2008-01-01`

### 6. Run API

- `cd src/api &&  python3 run_server.py`

