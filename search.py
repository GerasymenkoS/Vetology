from elasticsearch import Elasticsearch
from image_match.elasticsearch_driver import SignatureES

es = Elasticsearch()
ses = SignatureES(es)

def load_file(path):
    ses.add_image(path)

def search_file(file_bytes):
    return ses.search_image(file_bytes, bytestream=True)
