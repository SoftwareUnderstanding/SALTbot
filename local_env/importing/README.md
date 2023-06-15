 # Wikidata to Wikibase importer

This repository consists of two files:

* `Importing_entities.ipynb` notebook with documentation and possible implementations of different ways to import entities from Wikidata
* `importer2.py` a functional implementation of an importer 

**We recommend you go through `importer2.py` and edit these lines according to the wikibase you want to target**

```console
def change_config_wb():
    wbi_config['MEDIAWIKI_API_URL'] = 'http://localhost:80/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = 'http://localhost:8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    wbi_config['WIKIBASE_URL'] = 'http://localhost:80'
```

