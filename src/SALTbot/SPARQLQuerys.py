import time
from urllib.parse import urlparse

import requests


ARTICLES_ENDPOINT = 'https://query-scholarly.wikidata.org/sparql'
GENERAL_ENDPOINT = 'https://query.wikidata.org/sparql'
MAIN_ENDPOINT = 'https://query-main.wikidata.org/sparql'

DEFAULT_TIMEOUT = 60
SPARQL_REQUEST_INTERVAL = 0.5
SPARQL_HEADERS = {
    'Accept': 'application/sparql-results+json',
    'User-Agent': 'SALTbot/1.0'
}
_last_sparql_request = 0.0


def waitForSparqlRateLimit():
    """Wait between SPARQL requests to avoid hammering Wikidata endpoints."""
    global _last_sparql_request

    elapsed = time.monotonic() - _last_sparql_request
    remaining = SPARQL_REQUEST_INTERVAL - elapsed

    if remaining > 0:
        time.sleep(remaining)

    _last_sparql_request = time.monotonic()


def isDefaultWikidataConfig(config_data):
    """Return True when SALTbot is using Wikidata's default endpoints."""
    if config_data is None:
        return True

    mediawiki_api_url = config_data.get('MEDIAWIKI_API_URL', '')
    sparql_endpoint_url = config_data.get('SPARQL_ENDPOINT_URL', '')
    wikibase_url = config_data.get('WIKIBASE_URL', '')

    return (
        mediawiki_api_url in ['', 'https://www.wikidata.org/w/api.php']
        and sparql_endpoint_url in [
            '',
            'https://query.wikidata.org/',
            'https://query.wikidata.org/sparql',
            'https://query-main.wikidata.org/sparql'
        ]
        and wikibase_url in ['', 'https://www.wikidata.org']
    )


def getGeneralEndpoint(config_data=None):
    """Return the SPARQL endpoint for software/general Wikidata queries."""
    if config_data is None:
        return GENERAL_ENDPOINT

    configured_endpoint = config_data.get('SPARQL_ENDPOINT_URL', '')

    if configured_endpoint and not isDefaultWikidataConfig(config_data):
        return configured_endpoint

    return GENERAL_ENDPOINT


def getArticleEndpoint(config_data=None):
    """Return the SPARQL endpoint for scholarly article queries."""
    if isDefaultWikidataConfig(config_data):
        return ARTICLES_ENDPOINT

    return getGeneralEndpoint(config_data)


def getEndpointForTargetClass(target_class, man_nodes, config_data=None):
    """Choose the SPARQL endpoint according to the entity class being queried."""
    if target_class == man_nodes.get('scholarly article'):
        return getArticleEndpoint(config_data)

    return getGeneralEndpoint(config_data)


def escapeSparqlString(value):
    """Escape a Python value for use inside a SPARQL string literal."""
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )


def getMwapiEndpoint(config_data=None):
    """Return the host used by the SPARQL MWAPI service."""
    if isDefaultWikidataConfig(config_data):
        return "www.wikidata.org"

    if config_data is None:
        return "www.wikidata.org"

    for key in ["WIKIBASE_URL", "MEDIAWIKI_API_URL"]:
        configured_url = config_data.get(key, "")
        if configured_url:
            parsed_url = urlparse(configured_url)
            if parsed_url.netloc:
                return parsed_url.netloc

    return "www.wikidata.org"


def executeSelect(query, endpoint=GENERAL_ENDPOINT, timeout=DEFAULT_TIMEOUT):
    """Execute a SPARQL SELECT query and return the raw binding list."""
    waitForSparqlRateLimit()

    response = requests.get(
        endpoint,
        params={
            'query': query,
            'format': 'json'
        },
        headers=SPARQL_HEADERS,
        timeout=timeout
    )
    response.raise_for_status()
    data = response.json()
    return data.get('results', {}).get('bindings', [])


def sparql_getLicenses(config_data=None):
    """SPARQL equivalent of the license SPDX lookup in getOptionalNodes."""
    
    query = """
    SELECT ?spdx ?item WHERE {
        ?item wdt:P2479 ?spdx .
    }
    """

    bindings = executeSelect(
        query,
        endpoint=getGeneralEndpoint(config_data)
    )

    licenses = {}

    for binding in bindings:
        spdx = binding["spdx"]["value"]
        item_uri = binding["item"]["value"]
        qnode_license = item_uri.rstrip("/").split("/")[-1]
        licenses[spdx] = qnode_license

    return licenses


def sparql_getProgrammingLanguage(language_name, config_data=None):
    """SPARQL equivalent of the programming-language search in createSoftwareOperations."""
    safe_language_name = escapeSparqlString(language_name)

    query = f"""
    SELECT ?item ?itemLabel WHERE {{
      ?item wdt:P31/wdt:P279* wd:Q9143 .
      ?item rdfs:label ?label .
      FILTER(LANG(?label) = "en")
      FILTER(STR(?label) = "{safe_language_name}")

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    LIMIT 10
    """

    bindings = executeSelect(
        query,
        endpoint=getGeneralEndpoint(config_data)
    )

    for binding in bindings:
        label = binding.get("itemLabel", {}).get("value")

        if label and label == language_name:
            item_uri = binding["item"]["value"]
            return item_uri.rstrip("/").split("/")[-1]

    return None


def sparql_getMandatoryNodes(config_data=None):
    """SPARQL equivalent of SALTbotHandler.getMandatoryNodes API lookups."""
    query = """
    SELECT ?key ?entity WHERE {
      VALUES (?key ?labelText ?kind) {
        ("instance of" "instance of" "property")
        ("main subject" "main subject" "property")
        ("described by source" "described by source" "property")
        ("scholarly article" "scholarly article" "item")
        ("software category" "software category" "item")
        ("software" "software" "item")
      }

      ?entity rdfs:label ?label .
      FILTER(LANG(?label) = "en")
      FILTER(STR(?label) = ?labelText)

      BIND(STRAFTER(STR(?entity), "/entity/") AS ?entityId)
      FILTER(
        (?kind = "property" && STRSTARTS(?entityId, "P")) ||
        (?kind = "item" && STRSTARTS(?entityId, "Q"))
      )
    }
    """

    bindings = executeSelect(
        query,
        endpoint=getGeneralEndpoint(config_data)
    )

    mandatory_nodes = {}

    for binding in bindings:
        key = binding["key"]["value"]
        entity_uri = binding["entity"]["value"]
        mandatory_nodes[key] = entity_uri.rstrip("/").split("/")[-1]

    missing_nodes = [
        "instance of",
        "main subject",
        "described by source",
        "scholarly article",
        "software category",
        "software"
    ]
    missing_nodes = [
        node for node in missing_nodes
        if node not in mandatory_nodes
    ]

    if missing_nodes:
        raise TypeError(
            "Required Wikibase nodes were not found: "
            + ", ".join(missing_nodes)
        )

    return mandatory_nodes


def sparql_getOptionalNodes(config_data=None):
    """SPARQL equivalent of SALTbotHandler.getOptionalNodes API lookups."""
    optional_nodes = {
        "licenses": sparql_getLicenses(config_data),
        "code repository": None,
        "programming language": None,
        "download url": None,
        "license": None,
        "version control system": None,
        "web interface software": None,
        "Git": None,
        "GitHub": None,
        "DOI": None,
        "free software": None,
        "OpenAlex ID": None
    }

    query = """
    SELECT ?key ?entity WHERE {
      VALUES (?key ?labelText ?kind) {
        ("code repository" "source code repository URL" "property")
        ("programming language" "programmed in" "property")
        ("download url" "download URL" "property")
        ("download url" "download link" "property")
        ("license" "copyright license" "property")
        ("version control system" "version control system" "property")
        ("web interface software" "web interface software" "property")
        ("Git" "Git" "item")
        ("GitHub" "GitHub" "item")
        ("DOI" "DOI" "property")
        ("free software" "free software" "item")
        ("OpenAlex ID" "OpenAlex ID" "property")
      }

      ?entity rdfs:label ?label .
      FILTER(LANG(?label) = "en")
      FILTER(STR(?label) = ?labelText)

      BIND(STRAFTER(STR(?entity), "/entity/") AS ?entityId)
      FILTER(
        (?kind = "property" && STRSTARTS(?entityId, "P")) ||
        (?kind = "item" && STRSTARTS(?entityId, "Q"))
      )
    }
    """

    bindings = executeSelect(
        query,
        endpoint=getGeneralEndpoint(config_data)
    )

    for binding in bindings:
        key = binding["key"]["value"]
        entity_uri = binding["entity"]["value"]

        if optional_nodes.get(key) is None:
            optional_nodes[key] = entity_uri.rstrip("/").split("/")[-1]

    return optional_nodes


def sparql_getEntitiesByName(name, targetClass, man_nodes, opt_nodes, config_data=None):
    """SPARQL equivalent of SALTbotHandler.getEntitiesByName."""
    safe_name = escapeSparqlString(name)
    mwapi_endpoint = escapeSparqlString(getMwapiEndpoint(config_data))

    tracked_props = [
        man_nodes.get("instance of"),
        man_nodes.get("main subject"),
        man_nodes.get("described by source"),
        opt_nodes.get("DOI"),
        opt_nodes.get("code repository")
    ]
    tracked_props = [
        prop for prop in tracked_props
        if prop is not None
    ]

    values = "\n".join([
        f'(wdt:{prop} "{prop}")'
        for prop in tracked_props
    ])

    search_query = f"""
    SELECT ?item ?itemLabel WHERE {{
      SERVICE wikibase:mwapi {{
        bd:serviceParam wikibase:endpoint "{mwapi_endpoint}";
          wikibase:api "EntitySearch";
          mwapi:search "{safe_name}";
          mwapi:language "en".
        ?item wikibase:apiOutputItem mwapi:item.
        ?itemLabel wikibase:apiOutput mwapi:label.
      }}
    }}
    LIMIT 100
    """

    search_bindings = executeSelect(
        search_query,
        endpoint=getGeneralEndpoint(config_data)
    )

    candidate_labels = {}

    for binding in search_bindings:
        item_uri = binding["item"]["value"]
        item_id = item_uri.rstrip("/").split("/")[-1]
        label = binding.get("itemLabel", {}).get("value", item_id)
        candidate_labels[item_id] = label

    if candidate_labels == {}:
        return {}

    item_values = " ".join([
        f"wd:{item_id}"
        for item_id in candidate_labels.keys()
    ])

    query = f"""
    SELECT ?item ?prop ?value WHERE {{
      VALUES ?item {{ {item_values} }}
      ?item wdt:{man_nodes["instance of"]}+ wd:{targetClass} .

      OPTIONAL {{
        VALUES (?directProp ?prop) {{
          {values}
        }}
        ?item ?directProp ?value .
      }}
    }}
    LIMIT 100
    """

    bindings = executeSelect(
        query,
        endpoint=getEndpointForTargetClass(
            targetClass,
            man_nodes,
            config_data
        )
    )

    entities = {}

    for binding in bindings:
        item_uri = binding["item"]["value"]
        item_id = item_uri.rstrip("/").split("/")[-1]
        label = candidate_labels.get(item_id, item_id)

        if item_id not in entities:
            entities[item_id] = {
                "labels": {
                    "en": {
                        "value": label
                    }
                },
                "claims": {}
            }

        if "prop" not in binding or "value" not in binding:
            continue

        prop = binding["prop"]["value"]
        value = binding["value"]["value"]
        datatype = "string"
        datavalue = value

        if value.startswith("http://www.wikidata.org/entity/"):
            datatype = "wikibase-item"
            datavalue = {
                "id": value.rstrip("/").split("/")[-1]
            }
        elif prop == opt_nodes.get("DOI"):
            datatype = "external-id"
        elif prop == opt_nodes.get("code repository"):
            datatype = "url"

        claim = {
            "mainsnak": {
                "datatype": datatype,
                "property": prop,
                "datavalue": {
                    "value": datavalue
                }
            }
        }

        entities[item_id]["claims"].setdefault(prop, []).append(claim)

    return entities


def sparql_getEntitiesByRepositoryUrl(repository_url, targetClass, man_nodes, opt_nodes, config_data=None):
    """Return entities of targetClass that declare repository_url with the code repository property."""
    code_repository_property = opt_nodes.get("code repository")

    if code_repository_property in [None, [], ""]:
        return {}

    safe_repository_url = escapeSparqlString(repository_url)

    tracked_props = [
        man_nodes.get("instance of"),
        man_nodes.get("main subject"),
        man_nodes.get("described by source"),
        opt_nodes.get("DOI"),
        code_repository_property
    ]
    tracked_props = [
        prop for prop in tracked_props
        if prop is not None
    ]

    values = "\n".join([
        f'(wdt:{prop} "{prop}")'
        for prop in tracked_props
    ])

    if targetClass == man_nodes.get("software category") and man_nodes.get("software"):
        target_class_filter = f'?item wdt:{man_nodes["instance of"]}/wdt:P279* wd:{man_nodes["software"]} .'
    else:
        target_class_filter = f'?item wdt:{man_nodes["instance of"]}+ wd:{targetClass} .'

    query = f"""
    SELECT ?item ?itemLabel ?prop ?value WHERE {{
      ?item wdt:{code_repository_property} ?repositoryUrl .
      FILTER(STR(?repositoryUrl) = "{safe_repository_url}")
      {target_class_filter}

      OPTIONAL {{
        VALUES (?directProp ?prop) {{
          {values}
        }}
        ?item ?directProp ?value .
      }}

      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language "en".
      }}
    }}
    LIMIT 100
    """

    bindings = executeSelect(
        query,
        endpoint=getEndpointForTargetClass(
            targetClass,
            man_nodes,
            config_data
        )
    )

    entities = {}

    for binding in bindings:
        item_uri = binding["item"]["value"]
        item_id = item_uri.rstrip("/").split("/")[-1]
        label = binding.get("itemLabel", {}).get("value", item_id)

        if item_id not in entities:
            entities[item_id] = {
                "labels": {
                    "en": {
                        "value": label
                    }
                },
                "claims": {}
            }

        if "prop" not in binding or "value" not in binding:
            continue

        prop = binding["prop"]["value"]
        value = binding["value"]["value"]
        datatype = "string"
        datavalue = value

        if value.startswith("http://www.wikidata.org/entity/"):
            datatype = "wikibase-item"
            datavalue = {
                "id": value.rstrip("/").split("/")[-1]
            }
        elif prop == opt_nodes.get("DOI"):
            datatype = "external-id"
        elif prop == code_repository_property:
            datatype = "url"

        claim = {
            "mainsnak": {
                "datatype": datatype,
                "property": prop,
                "datavalue": {
                    "value": datavalue
                }
            }
        }

        entities[item_id]["claims"].setdefault(prop, []).append(claim)

    return entities
