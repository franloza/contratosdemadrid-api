import argparse

from elasticsearch import Elasticsearch
from elastic import search


def main():
    parser = argparse.ArgumentParser(description='CLI to load data to Elasticsearch')
    parser.add_argument('endpoint', choices=['search'])
    parser.add_argument('argument')
    controller(**vars(parser.parse_args()))


def controller(endpoint: str, argument: str):
    es = Elasticsearch([{'host': 'localhost', 'port': '9200'}])
    if endpoint == 'search':
        print(search(es, 'companies', argument))


if __name__ == '__main__':
    main()