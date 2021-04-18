#contratosdemadrid

## Getting started
### Extract

- `python3 src/etl/extract_csv.py --dir-path files/csv --start-date 2021-01-01`

### Transform

- `python3 src/etl/transform.py json --input-dir-path files/json --output-dir-path files/json --start-date 2021-01-01`

### Load
- `python3 src/etl/load.py companies --dir-path files/json --start-date 2021-01-01`
- `python3 src/etl/load.py contracts --dir-path files/json --start-date 2021-01-01`
