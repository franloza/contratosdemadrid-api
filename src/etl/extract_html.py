import re
import os
import http.client
import argparse
from datetime import datetime, timedelta

from bs4 import BeautifulSoup

# Constants
SEARCH_URL = "/cs/Satellite"
BASE_URL = "www.madrid.org"
CID_REGEX = r"cid=(\d+)"

def main():
    parser = argparse.ArgumentParser(description='CLI to download contracts information in HTML format')
    parser.add_argument('--start-date', type=valid_date, default=datetime(2008, 6, 1),
                        help="Start date (Format %Y-%m-%d")
    parser.add_argument('--end-date', type=valid_date, default=datetime.now(), help="End date (Format %Y-%m-%d")
    parser.add_argument('--dir-path', default=os.path.dirname(__file__), help="End date (Format %Y-%m-%d")
    extract(**vars(parser.parse_args()))


def valid_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def get_contract_urls(date: datetime, next_page=None, pages=None, urls=None):
    if pages is None:
        print(f"Date: {date.strftime('%d/%m/%Y')}")
    if urls is None:
        urls = []
    conn = http.client.HTTPConnection(BASE_URL)
    date_str = date.strftime('%d/%m/%Y')
    if next_page:
        conn.request("GET", next_page)
    else:
        payload = ("-----011000010111000001101001\r\n"
                   "Content-Disposition: form-data; "
                   "name=\"_charset_\"\r\n\r\nUTF-8\r\n"
                   "-----011000010111000001101001\r\n"
                   "Content-Disposition: form-data; "
                   "name=\"pagename\"\r\n\r\nPortalContratacion/Comunes/Presentacion/PCON_resultadoBuscadorAvanzado\r\n"
                   "-----011000010111000001101001\r\n"
                   "Content-Disposition: form-data; name=\"language\"\r\n\r\nes\r\n"
                   "-----011000010111000001101001\r\n"
                   f"Content-Disposition: form-d"
                   f""
                   f""
                   f"ata; name=\"fechaFormalizacionDesde\"\r\n\r\n{date_str}\r\n"
                   "-----011000010111000001101001\r\n"
                   f"Content-Disposition: form-data; name=\"fechaFormalizacionHasta\"\r\n\r\n{date_str}\r\n"
                   "-----011000010111000001101001--\r\n")
        headers = {
            'content-type': "multipart/form-data; boundary=---011000010111000001101001"
        }
        conn.request("POST", SEARCH_URL, payload, headers)
    res = conn.getresponse()
    data = res.read()
    html_doc = data.decode("utf-8")
    soup = BeautifulSoup(html_doc, 'html.parser')
    links = soup.find_all("a")
    for link in links:
        href = link.get("href")
        if href:
            if href.startswith("/cs/Satellite?c=CM_ConvocaPrestac_FA&"):
                urls.append("http://" + BASE_URL + href)
            elif not next_page and 'newPagina=' in href:
                if pages is None:
                    pages = [href]
                elif href not in pages:
                    pages.append(href)
    if pages:
        next_page = pages.pop()
        get_contract_urls(date, next_page, pages, urls)
    return urls


def extract(start_date: datetime, end_date: datetime, dir_path: str):
    day_count = (end_date - start_date).days + 1
    for date in [d for d in (start_date + timedelta(n) for n in range(day_count)) if d <= end_date]:
        urls = get_contract_urls(date)
        for url in urls:
            try:
                cid = re.search(CID_REGEX, url).groups()[0]
                idoc = None
            except Exception:
                cid = None
                idoc = url.split('&')[2].replace('idoc=', '')
            path = os.path.join(dir_path, date.strftime('%Y'), date.strftime('%m'), date.strftime('%d'),
                                f"{cid or idoc}.html")
            print(f"Downloading HTML file to {path}")
            download_html(url, path)


def download_html(url: str, path: str):
    conn = http.client.HTTPConnection(BASE_URL)
    conn.request("GET", url)
    res = conn.getresponse()
    data = res.read()
    html_doc = data.decode("utf-8")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    html_file = open(path, "w")
    html_file.write(html_doc)
    html_file.close()


if __name__ == '__main__':
    main()

