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

 ## Annex
 ### local_env directory
 In SALTbot/local_env, you can find scripts and documentation on how to create and populate your own local wikibase using docker
 
 ## Citation
 If you use SALTbot, please use the following citation:
 ```
 @software{Bolinches_SALTbot_Software_and_2023,
  author = {Bolinches, Jorge and Garijo, Daniel},
  doi = {10.5281/zenodo.8190001},
  month = jul,
  title = {{SALTbot: Software and Article Linker Toolbot}},
  url = {https://github.com/SoftwareUnderstanding/SALTbot},
  version = {v0.0.1},
  year = {2023}
  }
 ```

  
