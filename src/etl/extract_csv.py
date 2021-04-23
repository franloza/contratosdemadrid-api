import requests
import os
import argparse
from datetime import datetime, timedelta

# Constants
BASE_URL = "http://www.madrid.org/cs/FileServlet"


def main():
    parser = argparse.ArgumentParser(description='CLI to download contracts in CSV format')
    parser.add_argument('--start-date', type=valid_date, default=datetime(2008, 6, 1),
                        help="Start date (Format %Y-%m-%d")
    parser.add_argument('--end-date', type=valid_date, default=datetime.now(), help="End date (Format %Y-%m-%d")
    parser.add_argument('--dir-path', default=os.path.dirname(__file__), help="End date (Format %Y-%m-%d")
    parser.add_argument('--no-partition', action="store_true", help="Downloads the data in a single file")
    extract(**vars(parser.parse_args()))


def valid_date(s: str) -> datetime:
    try:
        return datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        msg = "Not a valid date: '{0}'.".format(s)
        raise argparse.ArgumentTypeError(msg)


def extract(start_date: datetime, end_date: datetime, dir_path: str, no_partition=False):
    if no_partition:
        start_date = (start_date - timedelta(days=1)).strftime('%Y-%m-%d')
        end_date = end_date.strftime('%Y-%m-%d')
        path = os.path.join(dir_path, f"{start_date}-{end_date}.csv")
        download_file(start_date, end_date, path)
    else:
        day_count = (end_date - start_date).days + 1
        for date in [d for d in (start_date + timedelta(n) for n in range(day_count)) if d <= end_date]:
            date_str = date.strftime('%Y-%m-%d')
            prev_date_str = (date - timedelta(days=1)).strftime('%Y-%m-%d')
            path = os.path.join(dir_path, date.strftime('%Y'), date.strftime('%m'), f"{date_str}.csv")
            download_file(prev_date_str, date_str, path)


def download_file(start_date: str, end_date: str, path: str):
    query_filter = f"FechaPublicacionAdjudicacion:[{start_date}T23:00:00.000Z+TO+{end_date}T22:59:59.999Z]"
    query = f"fq=({query_filter})"
    url = f"{BASE_URL}?{query}"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    print(f"Downloading data from {url} to {path}")
    r = requests.get(url, allow_redirects=True)
    with open(path, 'w') as f:
        f.write(r.content.decode("iso-8859-1"))


if __name__ == '__main__':
    main()
