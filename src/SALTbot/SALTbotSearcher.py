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
        bibtex_value = info["result"]["value"]
        if hasattr(bibtexparser, "loads"):
            parsed_bib = bibtexparser.loads(bibtex_value)
        else:
            parsed_bib = bibtexparser.parse_string(bibtex_value)

        if not parsed_bib.entries:
            return None, None

        entry = parsed_bib.entries[0]

        title = entry.get("title")
        doi = entry.get("doi")
        if hasattr(title, "value"):
            title = title.value
        if hasattr(doi, "value"):
            doi = doi.value

        return title, doi

    except Exception:
        return None, None


def queryOpenAlex(article):
    article = article.replace(",", "")
    url = 'https://api.openalex.org/works'
    #print(url)

    try:
        response = requests.get(
            url,
            params={'filter': 'title.search:' + article},
            timeout=60
        )
        r = response.json()
    except (requests.RequestException, ValueError) as e:
        print('OpenAlex query failed:', e)
        return None

    if r.get('meta', {}).get('count', 0)>0 and r.get('results'):
        return r['results'][0]
    else:
        return None

#returns all the article titles detected
#info: json extracted with somef
def parseTitles(info):
    parsedinfo = []
    DOIs = {}
    article_types = {
        "article",
        "journal-article",
        "journal article",
        "conference-paper",
        "conference paper",
        "paper",
        "proceedings-article",
        "proceedings article",
        "scholarlyarticle",
        "scholarly article"
    }

    if "citation" not in info:
        return parsedinfo, DOIs

    for citation in info["citation"]:

        techniques = citation["technique"]
        if not isinstance(techniques, list):
            techniques = [techniques]

        if not any(technique in [
            "file_exploration",
            "regular_expression"
        ] for technique in techniques):
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

            citation_type = str(
                citation_data.get("type", "")
                or citation["result"].get("type", "")
            ).lower()
            if citation_type not in article_types:
                continue

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
