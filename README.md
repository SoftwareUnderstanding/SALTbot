# SALTbot: Software and Article Linker Toolbot
[![Project Status: Active – The project has reached a stable, usable state and is being actively developed.](https://www.repostatus.org/badges/latest/active.svg)](https://www.repostatus.org/#active) [![DOI](https://zenodo.org/badge/490763453.svg)](https://zenodo.org/badge/latestdoi/490763453)


## DESCRIPTION

  This repository contains the implementation of a tool designed to link Scientific Articles and their Software pages on Wikibase graphs.
  
  SALTBot is proposed as a Wikidata bot, with its own page [here](https://www.wikidata.org/wiki/User:SALTbot). It is maintained and run by the Ontology Engineering Group and Universidad Politécnica de Madrid.

## INSTALLATION
  
  It is required to have an environment with at least Python 3.9
  
  1-. Clone repository
  
  2-. Install requirements
  ```console
  pip install -r requirements.txt
  ```
  3-. Install and configure [SOMEF](https://github.com/KnowledgeCaptureAndDiscovery/somef/) a Python library for extracting software metadata from a code repository.
  https://github.com/KnowledgeCaptureAndDiscovery/somef
  
 
  
## USAGE
### Configure
Before running SALTbot, you must first configure your login credentials and wikibase using the configure command
```console
python SALTbot.py configure
```
You can invoke this command using -a as argument to skip the Wikibase configuration and target Wikidata automatically 
SALTbot will then prompt you for you login information and the required wikibase URLs. If left blank, the URLs will default to Wikidata's respective values
An example of the Wikibase configuration using Wikidatas values would be the following

```console
MEDIAWIKI_API_URL = https://www.wikidata.org/w/api.php
SPARQL_ENDPOINT_URL = https://query.wikidata.org/
WIKIBASE_URL = https://www.wikidata.org
```
### Running
Once configured, execute SALTbot using

```console
python SALTbot.py run  [ARGS]
```

 For more info, run:
 ```console
 python SALTbot.py [COMMAND] --help
 ```
 
 ## Citation
 If you use SALTbot, please use the following citation:
 ```
 @article{bolinches2023saltbot,
  title		   = {SALTBot: Linking Software and Articles in Wikidata},
  author	   = {Bolinches, Jorge and Garijo, Daniel},
  year         = {2023},
  booktitle    = {Proceedings of the Wikidata Workshop 2023 co-located with 22nd International Semantic Web Conference (ISWC 2023)},
  publisher    = {CEUR-WS.org},
  series       = {{CEUR} Workshop Proceedings},
  volume       = {3640},
  url          = {https://ceur-ws.org/Vol-3640/paper12.pdf}
}

 ```

  
