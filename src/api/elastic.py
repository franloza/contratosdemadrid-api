from elasticsearch import Elasticsearch


def search(es: Elasticsearch, index_name: str, query: str):
    return es.search(index=index_name, body={
        "query": {
            "query_string": {
              "query": query,
              "analyze_wildcard": True,
              "default_field": "*"
            }
        }
    })


def get_by_id(es: Elasticsearch, index_name: str, doc_id: str):
    return es.search(index=index_name, body={
        "query": {
            "terms": {
                "_id": [doc_id]
            }
        }
    })

