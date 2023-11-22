import gscholar
from util import *

def get_bibtex_from_title(title):
    try:
        return gscholar.query(title)[0]
    except:
        print(f"Error: Unable to get BibTeX for title: {title}")
        return 'None'
    
# 读取yaml
import yaml
from yaml.loader import SafeLoader
import os
# 读取yaml函数
def load_data(filename):
    file = open(filename, encoding="utf8")
    try:
        with file:
            data = yaml.load(file, Loader=SafeLoader)
    except Exception:
        raise Exception(f"Can't parse {filename}. Make sure it's valid YAML.")
    # if no errors, return data
    return data

if __name__=="__main__":
    citations = load_data("../_data/citations.yaml")
    for citation in citations:
        title = citation['title']
        doi = citation['id']
        bibtex = get_bibtex_from_title(title)
        save_bibtex(doi, bibtex)