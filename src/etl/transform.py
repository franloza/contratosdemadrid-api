from io import StringIO
import json
import os
import argparse
from datetime import datetime
import glob
import csv
import locale
import os

from bs4 import BeautifulSoup


def main():
    parser = argparse.ArgumentParser(description='CLI to transform data from CSV or HTML files')
    parser.add_argument('format', choices=['csv', 'html'])
    parser.add_argument('--start-date', type=valid_date, default=datetime(2008, 6, 1),
                        help="Start date (Format %Y-%m-%d")
    parser.add_argument('--end-date', type=valid_date, default=datetime.now(), help="End date (Format %Y-%m-%d")
    parser.add_argument('--input-dir-path', default=os.path.dirname(__file__))
    parser.add_argument('--output-dir-path', default=os.path.dirname(__file__))
    transform(**vars(parser.parse_args()))


def valid_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def transform(format: str, start_date: datetime, end_date: datetime, input_dir_path: str, output_dir_path: str):
    if format == "csv":
        csv.register_dialect('custom', delimiter=';')
        for filename in glob.iglob(input_dir_path + '/**/*.csv', recursive=True):
            date_str = os.path.basename(filename).replace('.csv', '')
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if start_date <= date <= end_date:
                data = transform_csv(filename, date_str)
                output_path = os.path.join(output_dir_path, date.strftime('%Y'), date.strftime('%m'), f"{date_str}.json")
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                print(f"Transforming data from {filename} to {output_path}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=4)
    else:
        previous_date_str = None
        data = []
        for filename in sorted(glob.iglob(input_dir_path + '/**/*.html', recursive=True)):
            date_str = "-".join(filename.split('/')[-4:-1])
            cid = os.path.basename(filename).replace('.html', '')
            if previous_date_str is not None and previous_date_str != date_str:
                # Write to disk
                if data:
                    previous_date = datetime.strptime(previous_date_str, "%Y-%m-%d")
                    output_path = os.path.join(output_dir_path, previous_date.strftime('%Y'),
                                               previous_date.strftime('%m'),
                                               f"{previous_date_str}.json")
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    print(f"Writing data to {output_path}")
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=4)
                    data = []
            previous_date_str = date_str
            date = datetime.strptime(date_str, "%Y-%m-%d")
            if start_date <= date <= end_date:
                contract = transform_html(filename, cid)
                data.append(contract)


def transform_html(filename, cid) -> dict:
    locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    with open(filename, 'r') as f:
        contents = f.read()
        soup = BeautifulSoup(contents, 'html.parser')
        contract = {
            "titulo": soup.find("h2", {"class", "tit11gr3"}).string
        }
        soup.find("h2", {"class", "tit11gr3"})
        contract_attr_lists = soup.findAll("div", {"class": "listado"})
        for contract_attr_list in contract_attr_lists:
            contract_attrs = contract_attr_list.findAll("li", {"class": "txt08gr3"})
            total_vat_included = 0
            awardees = []
            for attr in contract_attrs:
                for linebreak in attr.find_all('br'):
                    linebreak.extract()
                if attr.find("strong") is not None:
                    attr_name = attr.find("strong").string.replace("\n", "")
                    attr.find("strong").extract()
                    attr_value = attr.text.replace("\n", "")
                    attr_mapping = {
                        "Estado de la licitación": "estado",
                        "Tipo resolución": "tipo-resolucion",
                        "Objeto del contrato": "objeto-contrato",
                        "Código CPV": "codigo-cpv",
                        "Tipo Publicación": "actuacion",
                        "Número de expediente": "numero-expediente",
                        "Referencia": "referencia",
                        "Tipo de contrato": "tipo",
                        "Código NUTS": "codigo-nuts",
                        "Procedimiento Adjudicación": "procedimiento",
                        "Valor estimado sin I.V.A": "importe-sin-iva",
                        "Presupuesto base licitación (sin impuestos)": "presupuesto-sin-iva",
                        "Presupuesto base licitación. Importe total": "presupuesto-con-iva",
                        "Duración del contrato": "duracion",
                    }
                    if attr_name in attr_mapping:
                        contract[attr_mapping[attr_name]] = attr_value
                    elif attr_name == "Compra pública innovadora":
                        contract["compra-innovadora"] = False if attr_value == "No" else True
                    elif attr_name in ("Formalización del contrato publicada el", "Contrato desierto el"):
                        contract["fecha-formalizacion"] = parse_contract_date(attr_value)
                    elif attr_name == "Adjudicación del contrato publicada el":
                        contract["fecha-adjudicacion"] = parse_contract_date(attr_value)
                    elif attr_name in (
                            "Fecha límite de presentación de ofertas o solicitudes de participación",
                            "Defectos u omisiones de la documentación publicados el",
                            "Ofertas anormales o desproporcionadas publicadas el"):
                        pass
                    elif attr_name in ("Fecha publicación de la licitación en el BOCM", "Formalización del contrato publicada en BOCM el"):
                        contract["fecha-publicacion"] = parse_contract_date(attr_value)
                    elif attr_name == "Entidad adjudicadora":
                        if "→" in attr_value:
                            entity = attr_value.split("→")
                        else:
                            entity = attr_value.split('··>')
                        contract['organo'] = " > ".join(entity[0:2]).strip()
                        contract['suborgano'] = entity[2].strip() if len(entity) > 2 else None
                    elif attr_name in ("Puntos de Información", "Otros Anuncios", "Modalidad"):
                        pass
                    else:
                        print(f"Attribute skipped: {attr_name} - {attr_value}. CID: {cid}")
                elif attr.find("table", {"class": "tableAdjudicacion"}) is not None:
                    table = attr.find("table", {"class": "tableAdjudicacion"})
                    header = table.find("thead").extract()
                    rows = table.findAll("tr")
                    if header.find("th").find("span").string == "RESULTADOS DE LA LICITACIÓN":
                        for row in rows:
                            cells = row.findAll("td")
                            result = cells[2].string
                            if result not in ("Desierto", "Desistimiento"):
                                awardee = {
                                    "lote": cells[0].string,
                                    "num-ofertas": int(cells[1].string),
                                    "resultado": result,
                                    "nif": cells[3].string,
                                    "name": cells[4].string,
                                    "vat_excluded": float(cells[5].string.replace(".", "").replace(",", ".")),
                                    "vat_included": float(cells[6].string.replace(".", "").replace(",", ".")),
                                }
                                total_vat_included += awardee["vat_included"]
                                awardees.append(awardee)
                else:
                    raise ValueError(f"Attribute not expected: {attr}")
        contract["url"] = ("http://www.madrid.org/cs/Satellite?"
                           "c=CM_ConvocaPrestac_FA&"
                           f"cid={cid}"
                           "&definicion=Contratos+Publicos"
                           "&language=es"
                           "&op2=PCON"
                           "&pagename=PortalContratacion%2FPage%2FPCON_contratosPublicos"
                           "&tipoServicio=CM_ConvocaPrestac_FA")
        # Convert types
        for key in ("importe-sin-iva", "presupuesto-sin-iva", "presupuesto-con-iva"):
            contract[key] = (float(contract[key].replace(" euros", "").replace(".", "").replace(",", "."))
                             if key in contract else None)
        contract["importe-con-iva"] = total_vat_included
        contract["adjudicatario"] = awardees
        contract["cid"] = cid
        return contract


def parse_contract_date(date_str) -> str:
    date_list = date_str.strip().split(" ")
    date_list[1] = date_list[1].capitalize()
    date_str = " ".join(date_list)
    return datetime.strptime(date_str, '%d %B %Y').strftime("%Y-%m-%d")


def transform_csv(filename, date) -> list:
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
            "nif": row["NIF ADJUDICATARIO"].replace('-', '').replace(' ', '').strip()
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
                "fecha-formalizacion": date,
                'url': (f"http://www.madrid.org/cs/Satellite?"
                                      f"pagename=PortalContratacion/Comunes/Presentacion/PCON_resultadoBuscadorAvanzado"
                                      f"&referencia={row['REFERENCIA']}&numeroExpediente={row['Nº EXPEDIENTE']}")
            }
        else:
            contracts[row['REFERENCIA']]['adjudicatario'].append(adjudicatario)
            contracts[row['REFERENCIA']]['importe-con-iva'] += importe
    return list(contracts.values())

if __name__ == '__main__':
    main()
