from hashlib import sha1
from io import StringIO
from elasticsearch import Elasticsearch, NotFoundError
import os
import argparse
from datetime import datetime, timedelta
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
    for filename in glob.iglob(dir_path + '/**/*.csv', recursive=True):
        date_str = os.path.basename(filename).replace('.csv', '')
        date = datetime.strptime(date_str, "%Y-%m-%d")
        if start_date <= date <= end_date:
            data = transform(filename, date_str)
            if index_type == "companies":
                print(f"Loading companies for day {date_str}")
                load_companies(es, data)
            elif index_type == "contracts":
                print(f"Loading contracts for day {date_str}")
                load_contracts(es, data)
            else:
                raise NotImplemented()


def transform(filename, date) -> list:
    contracts = {}
    with open(filename, 'r', encoding="utf-8") as file:
        content = StringIO(file.read().replace('&#160;', ''))
    csv_file = csv.DictReader(content, dialect='custom')
    for row in csv_file:
        try:
            importe = float(row['IMPORTE DE ADJUDICACIÓN(CON IVA)'].replace('.', '').replace(',', '.'))
        except ValueError:
            importe = 0
        except KeyError:
            print(f"The file corresponding to date {date} has not a valid format. Skipping")
            return []
        try:
            presupuesto = float(row['PRESUPUESTO DE LICITACIÓN(CON IVA)'].replace('.', '').replace(',', '.'))
        except ValueError:
            presupuesto = 0

        adjudicatario = {
            "name": row['ADJUDICATARIO'],
            "vat_excluded": importe / 1.21,
            "vat_included": importe,
            "nif": row["NIF ADJUDICATARIO"].replace('-', '').strip()
        }
        if (row['REFERENCIA']) not in contracts:
            entity = row['ENTIDAD ADJUDICADORA'].split('··>')
            contracts[row['REFERENCIA']] = {
                'titulo': row['OBJETO DEL CONTRATO'],
                'referencia': row['REFERENCIA'],
                'actuacion': row['TIPO DE PUBLICACIÓN'],
                'tipo': row['TIPO CONTRATO'],
                'organo': " > ".join(entity[0:2]),
                'suborgano': entity[2] if len(entity) > 2 else None,
                'numero-expediente': row['Nº EXPEDIENTE'],
                'procedimiento': row['PROCEDIMINETO DE ADJUDICACIÓN'],
                'presupuesto-con-iva': presupuesto,
                'importe-con-iva': importe,
                'adjudicatario': [adjudicatario],
                "fecha-formalizacion": date
            }
        else:
            contracts[row['REFERENCIA']]['adjudicatario'].append(adjudicatario)
            contracts[row['REFERENCIA']]['importe-con-iva'] += importe
    return list(contracts.values())


def load_companies(es: Elasticsearch, data: list):
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
