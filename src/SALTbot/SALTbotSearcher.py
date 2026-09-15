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
import requests
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup


def parseBib(info):
    try:
        parsed_bib = bibtexparser.loads(info["result"]["value"])

        if not parsed_bib.entries:
            return None, None

        entry = parsed_bib.entries[0]

        title = entry.get("title")
        doi = entry.get("doi")

        return title, doi

    except Exception:
        return None, None


def queryOpenAlex(article):
    article = article.replace(",", "")
    url = 'https://api.openalex.org/works?filter=title.search:'+ article
    #print(url)

    r = requests.get(url).json()

    if r['meta']['count']>0:
        return r['results'][0]
    else:
        return None

#returns all the article titles detected
#info: json extracted with somef
def parseTitles(info):
    parsedinfo = []
    DOIs = {}

    if "citation" not in info:
        return parsedinfo, DOIs

    for citation in info["citation"]:

        if citation["technique"] not in [
            "file_exploration",
            "regular_expression"
        ]:
            continue

        value = citation["result"]["value"].strip()

        # BibTeX
        if value.startswith("@"):
            title, doi = parseBib(citation)

            if title:
                print(
                    "DETECTED TITLE:",
                    title,
                    "     TECHNIQUE:",
                    citation["technique"]
                )

                parsedinfo.append(title)

                if doi:
                    DOIs[doi] = title

            continue

        # YAML / CITATION.cff
        try:
            parsed_yaml = yaml.load(
                value,
                Loader=SafeLoader
            )

            if not isinstance(parsed_yaml, dict):
                continue

            if "preferred-citation" in parsed_yaml:
                citation_data = parsed_yaml["preferred-citation"]
            else:
                citation_data = parsed_yaml

            title = citation_data.get("title")

            if title:
                print(
                    "DETECTED TITLE:",
                    title,
                    "     TECHNIQUE:",
                    citation["technique"]
                )

                parsedinfo.append(title)

            doi = citation_data.get("doi") or citation_data.get("DOI")

            if doi and title:
                DOIs[doi] = title

        except Exception as e:
            print(e)

    return parsedinfo, DOIs
