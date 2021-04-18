from hashlib import sha1
import json
from elasticsearch import Elasticsearch, NotFoundError
import os
import argparse
from datetime import datetime
import glob
import csv

# Constants
COMPANIES_INDEX_NAME = 'companies'
CONTRACTS_INDEX_NAME = 'contracts'


def main():
    parser = argparse.ArgumentParser(description='CLI to load data to Elasticsearch')
    parser.add_argument('index_type', choices=['companies', 'contracts'])
    parser.add_argument('--start-date', type=valid_date, default=datetime(2008, 6, 1),
                        help="Start date (Format %Y-%m-%d")
    parser.add_argument('--end-date', type=valid_date, default=datetime.now(), help="End date (Format %Y-%m-%d")
    parser.add_argument('--dir-path', default=os.path.dirname(__file__), help="End date (Format %Y-%m-%d")
    load(**vars(parser.parse_args()))


def valid_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def load(index_type: str, start_date: datetime, end_date: datetime, dir_path: str):
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    csv.register_dialect('custom', delimiter=';')
    for filename in glob.iglob(dir_path + '/**/*.json', recursive=True):
        date_str = os.path.basename(filename).replace('.json', '')
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if start_date <= date <= end_date:
            with open(filename) as json_file:
                data = json.load(json_file)
            if index_type == "companies":
                print(f"Loading companies for day {date_str}")
                load_companies(es, data)
            elif index_type == "contracts":
                print(f"Loading contracts for day {date_str}")
                load_contracts(es, data)
            else:
                raise NotImplemented()


def load_companies(es: Elasticsearch, data: list):
    #es.indices.delete(index=COMPANIES_INDEX_NAME)
    es.indices.create(index=COMPANIES_INDEX_NAME, ignore=400)
    for contract in data:
        for company in contract['adjudicatario']:
            doc = {
                "nombre": company["name"],
                "nif": company["nif"],
                "aliases": company["name"]
            }
            doc_id = get_doc_id(doc, fields=['nif'])
            es.update(
                index=COMPANIES_INDEX_NAME,
                doc_type='_doc',
                body={
                    "upsert": doc,
                    "script": {
                        "source":
                            """
                            if(! ctx._source.aliases.contains(params.name)) {
                                ctx._source.aliases += ", " + params.name
                            }  
                            """,
                        "params": {"name": company["name"]}
                    }
                },
                id=doc_id)


def load_contracts(es: Elasticsearch, data: list):
    #es.indices.delete(index=CONTRACTS_INDEX_NAME)
    es.indices.create(index=CONTRACTS_INDEX_NAME, ignore=400, body={
        "mappings": {
            "properties": {
                "adjudicatario": {
                    "type": "nested",
                }
            }
        }
    })
    for contract in data:
        for idx, company in enumerate(contract['adjudicatario']):
            doc_id = get_doc_id(company, fields=['nif'])
            try:
                es.get(index=COMPANIES_INDEX_NAME, doc_type="_doc", id=doc_id)
                contract['adjudicatario'][idx]["id"] = doc_id
            except NotFoundError:
                print(f"Skipping contract linked to company with NIF {company['nif']}. Company not found")
        contract_id = get_doc_id(contract, fields=['referencia', 'numero-expediente'])
        es.update(
            index=CONTRACTS_INDEX_NAME,
            doc_type='_doc',
            body={
                "doc": contract,
                "doc_as_upsert": True
            },
            id=contract_id)


def get_doc_id(doc: dict, fields):
    return sha1(repr(sorted((key, val) for key, val in doc.items() if key in fields)).encode()).hexdigest()


if __name__ == '__main__':
    main()
