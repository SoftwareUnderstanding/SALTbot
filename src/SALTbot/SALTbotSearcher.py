import bibtexparser
import yaml
from yaml.loader import SafeLoader
from urllib.parse import urlparse

from wikibaseintegrator import wbi_login
#from wikiintegrator import wbi_core
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.datatypes import ExternalID, Item, String, URL, Quantity, Property, CommonsMedia, GlobeCoordinate
from wikibaseintegrator.models import Qualifiers
from wikibaseintegrator.wbi_enums import ActionIfExists

import time
import json
import re

import pandas as pd
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup


def parseBib(info):
    try:
        bibparse = bibtexparser.loads(info["result"]["value"])
        parsedtitle = parsedbib.entries[0]["title"]
        print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
    except Exception as e:
        return None
    parsedinfo.append(parsedtitle)

def parseTitles(info):
    parsedinfo = []
    authors = {}
    DOIs = {}

    # For each extraction technique
    if "citation" in info.keys():
        for i in info["citation"]:


            #If it is File Exploration or Regular expression
            if(i["technique"] == "file_exploration" or i["technique"] == "regular_expression"):
                
            
                #try parsing to BIB
                try:
                    parsed = parseBib(i)
                    parsedtitle = parsedbib.entries[0]["title"]
                    #print(parsedbib.entries)
                    print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
                    parsedinfo.append(parsedtitle)
                except Exception as e:
                    #print(e)
                #try parsing to YAML
                
                    try:
                        parsedyaml = yaml.load(i["result"]["value"], Loader = SafeLoader)
                        #print(parsedyaml.keys())
                        if('preferred-citation' in parsedyaml.keys()):
                            #print('yaml: ', parsedyaml['preferred-citation'])
                            author_count = 0
                            parsedtitle = parsedyaml['preferred-citation']['title']

                            if 'authors' in parsedyaml['preferred-citation'].keys():
                                for author in parsedyaml['preferred-citation']['authors']:
                                    authors.update({author_count:author})
                                    author_count =  author_count +1
                            if 'doi' in parsedyaml['preferred-citation'].keys():
                                DOIs.update({parsedyaml['preferred-citation']['doi']:parsedtitle})
                            elif 'DOI' in parsedyaml['preferred-citation'].keys():
                                DOIs.update({parsedyaml['preferred-citation']['DOI']:parsedtitle})
                            
                        else:
                            parsedtitle = parsedyaml["title"]
                        #print(parsedyaml['preferred-citation']['title'])
                        #print("yaml")
                        print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
                        parsedinfo.append(parsedtitle)
                    except Exception as e:
                        print(e)  
                        
                
    #print('authors:', authors)
    
    return parsedinfo, DOIs
