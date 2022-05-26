# SALTbot: Software and Article Linker Toolbot
[![Project Status: WIP – Initial development is in progress, but there has not yet been a stable, usable release suitable for the public.](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip)


## DESCRIPTION

  
  This repository contains the implementation of a bot capable of linking Scientific Articles and their Software pages on Wikidata

## INSTALATION

  It is required to have an environment with Python 3.9 
  
  ### -SOMEF (https://github.com/KnowledgeCaptureAndDiscovery/somef) 
  run:
  
    >pip install somef
  
    >somef configure
  
  ### -PyYAML
  run:
   
    >pip install pyyaml
  
  ### -BibTexParser
  run:
  
    >pip install bibtexparser
  
  ### -CLICK
  run:
  
    >pip install click
  
    >pip install click.opt.group
  
  ### -Pywikibot (https://github.com/wikimedia/pywikibot)
  run:
  
    >git clone https://github.com/wikimedia/pywikibot
  
    >cd pywikibot
  
    >python pwb.py login.py
  
   **When propmted:**
   
   1-.Choose Wikidata (number 14) as family of sites
   
   2-.Choose test as the site of code we are working on
   
   3-.Introduce your Wikidata username
   
   4-.(OPTIONAL) Introduce your bot password. This allows to modify the permissions of Pywikibot. 
        If introduced, you will not have to introduce your user password each time Pywikibot logs off. For creating one, go to: https://test.wikidata.org/wiki/Special:BotPasswords
  
  
## USAGE

  ### **python PATH_TO_pwb.py SALTbot.py [ARGS]** 
  
  Note: if you want to actually edit the test instance of wikidata, manually edit the values of the desired target qnodes (qnode_article_test, qnode_software_test) and properties (main_subject_test, described_by_source_test) to use, and change upload to True in SALTbot.py main.
