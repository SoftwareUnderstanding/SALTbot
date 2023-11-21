import bibtexparser
import yaml
from yaml.loader import SafeLoader
from urllib.parse import urlparse

from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
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

import SALTbotUpdater
import SALTbotSearcher
import SALTbotStatementDefiner

def getCorrectQnode(name, Qnodes):
    result = None
    for i in Qnodes:
        if i['label'] == name:
            result = i['id']
        #print(result)
    if result == None and name in ['instance of', 'main subject', 'described by source', 'scholarly article', 'software category', 'software']:
        raise TypeError(str(name)+" was not found on target Wikibase")
    return result

#TODO: change excepts  
def getOptionalNodes(wbi, configData):
    opt_nodes = {}
    opt_nodes['licenses'] = {}


    if (configData['MEDIAWIKI_API_URL'] == '' and configData['SPARQL_ENDPOINT_URL']=='' and configData['WIKIBASE_URL']=='') or (configData['MEDIAWIKI_API_URL'] == 'https://www.wikidata.org/w/api.php' and configData['SPARQL_ENDPOINT_URL']=='https://query.wikidata.org/' and configData['WIKIBASE_URL']=='https://www.wikidata.org'):
       {'licenses': {}, 'code repository': 'P1324', 'programming language': 'P277', 'download url': 'P4945', 'license': 'P275', 'version control system': 'P8423', 'web interface software': 'P10627', 'Git': 'Q186055', 'GitHub': 'Q82066181', 'DOI': 'P356', 'free software': 'Q341'}
    else:
        aux = 0
        try:
            opt_nodes['code repository'] = getCorrectQnode('source code repository URL', wbi_helpers.search_entities(search_string='source code repository URL', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['programming language'] = getCorrectQnode('programmed in', wbi_helpers.search_entities(search_string='programming language', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['download url'] = getCorrectQnode('download link', wbi_helpers.search_entities(search_string='download url', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['license'] = getCorrectQnode('copyright license', wbi_helpers.search_entities(search_string='license', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['version control system'] = getCorrectQnode('version control system', wbi_helpers.search_entities(search_string='version control system', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['web interface software'] = getCorrectQnode('web interface software', wbi_helpers.search_entities(search_string='web interface software', dict_result = True,search_type='property'))
        except:
            aux = 1
        try:
            opt_nodes['Git'] = getCorrectQnode('Git',wbi_helpers.search_entities(search_string='Git', dict_result=True, search_type='item'))
        except:
            aux = 1
        try:
            opt_nodes['GitHub'] = getCorrectQnode('GitHub',wbi_helpers.search_entities(search_string='GitHub', dict_result = True, search_type='item'))
        except:
            aux = 1
        try:
            opt_nodes['DOI'] = getCorrectQnode('DOI', wbi_helpers.search_entities(search_string='DOI', dict_result=True, search_type='property'))
        except:
            aux = 1
        try: 
            opt_nodes['free software'] = getCorrectQnode('free software', wbi_helpers.search_entities(search_string='free software', dict_result = True,search_type='item'))
        except:
            aux = 1
    
    #TODO:change Pnode for local
    #print(opt_nodes)
    try:
        query_license = ''' SELECT ?spdx ?item WHERE {?item wdt:P2479 ?spdx.}'''
        results = wbi_helpers.execute_sparql_query(query_license)
        licenses = {}
        for i in results['results']['bindings']:
            qnode_license = urlparse(i['item']['value']).path.replace("/", " ").split()[1]
            licenses.update({i['spdx']['value']:qnode_license})
        opt_nodes['licenses'] = licenses
    except Exception as e:
        print('No licenses found')
    
    return opt_nodes
       
def getMandatoryNodes(wbi, configData):
    prop_map = {}

    if (configData['MEDIAWIKI_API_URL'] == '' and configData['SPARQL_ENDPOINT_URL']=='' and configData['WIKIBASE_URL']=='') or (configData['MEDIAWIKI_API_URL'] == 'https://www.wikidata.org/w/api.php' and configData['SPARQL_ENDPOINT_URL']=='https://query.wikidata.org/' and configData['WIKIBASE_URL']=='https://www.wikidata.org'):
        prop_map={'instance of': 'P31', 'main subject': 'P921', 'described by source': 'P1343', 'scholarly article': 'Q13442814', 'software category': 'Q17155032', 'software': 'Q7397'}
    
    else:
        try:

            prop_map['instance of'] = getCorrectQnode('instance of', wbi_helpers.search_entities(search_string='instance of', dict_result = True,search_type='property'))
            prop_map['main subject'] = getCorrectQnode('main subject', wbi_helpers.search_entities(search_string='main subject', dict_result = True,search_type='property'))	
            prop_map['described by source'] = getCorrectQnode('described by source', wbi_helpers.search_entities(search_string='described by source', dict_result = True,search_type='property'))
            prop_map['scholarly article'] = getCorrectQnode('scholarly article', wbi_helpers.search_entities(search_string='scholarly article', dict_result = True,search_type='item'))	
            prop_map['software category'] = getCorrectQnode('software category', wbi_helpers.search_entities(search_string='software category', dict_result = True,search_type='item'))
            prop_map['software'] = getCorrectQnode('software', wbi_helpers.search_entities(search_string='software', dict_result = True,search_type='item'))

            
        except Exception as e:
            print('SALTbot Error: one or more of the required entities and properties has not been found in the target wikibase')
            print(e)
            raise(e)
        
    #print(prop_map)
    return prop_map
#gets possible pnodes of target wikibase to create software pages and returns a list with all the possible statements for that software




#Returns all entities related to entityQnode of class targetClass in the given wikibase
def getRelatedEntities(entityJSON, candidates, property=None): 
    entities = []
    if property==None:
        for prop in entityJSON['claims']:
            for statement in entityJSON['claims'][prop]:
                if statement['mainsnak']['datatype']=='wikibase-item' and statement['mainsnak']['datavalue']['value']['id'] in candidates.keys():
                    entities.append([statement['mainsnak']['datavalue']['value']['id'],candidates[statement['mainsnak']['datavalue']['value']['id']]['labels']['en']['value'], statement['mainsnak']['property']])
            
    return entities


# queries the graph for entities with name, which are instance of targetClass. The instance_of pnode has to be passed for integration with other wikibases
def getEntitiesByName(name, targetClass, man_nodes, wbi):

    entities={}

    results_wbi_helper = wbi_helpers.search_entities(search_string=name, dict_result=True, search_type='item')
    
    for i in results_wbi_helper:
        #print(i['description'])      
        query = '''ASK {wd:'''+i['id']+''' wdt:'''+man_nodes['instance of']+'''+ wd:'''+targetClass+'''}'''
        match = wbi_helpers.execute_sparql_query(query)

        if(str(match['boolean'])=='True' and i['id'] not in entities.keys()):
            entities.update({i['id']:wbi.item.get(entity_id=i['id']).get_json()})

    return(entities)
    

#returns all the article titles detected
#info: json extracted with somef

#info: json extracted with somef
#wbi: wbi object with all the graph related info
#articleQnode: the article Qnode in the target wikibase
#softwareQnode: the software Qnode in target wikibase
#instanceofPnode: the instance_of property pnode in target wikibase
#TODO: change operation printing format
def SALTbot(wbi, info, man_nodes, opt_nodes, auto, results):

    print("\n")
    click.echo(click.style('SEARCH', fg='red', bold=True))
    print("\n")

    #print(man_nodes)
    #print(opt_nodes)


    articles = {"TITLE EXTRACTION":{}, "REPO NAME":{}}
    softwares = {"TITLE EXTRACTION":{}, "REPO NAME":{}}

    parsedTitles, DOIs = SALTbotSearcher.parseTitles(info)

    results.update({info['code_repository'][0]['result']['value']:{'repo-article':[], 'article':None, 'software':None, 'article-software-link':False, 'software-article-link':False}})

    if(parsedTitles == []):
        print("NO DETECTED TITLES")
    else:   
        for title in parsedTitles:       
            articles['TITLE EXTRACTION'].update(getEntitiesByName(title,man_nodes['scholarly article'], man_nodes, wbi))
            results[info['code_repository'][0]['result']['value']]['repo-article'].append(title)
            
    name = info['name'][0]['result']['value']

    if(articles['TITLE EXTRACTION']=={}):
        articles['REPO NAME'].update(getEntitiesByName( name,man_nodes['scholarly article'], man_nodes, wbi))
    

    articles = articles['REPO NAME'] | articles['TITLE EXTRACTION']

    if parsedTitles != []: #and articles != {})
        for title in parsedTitles: 
            softwares['TITLE EXTRACTION'].update(getEntitiesByName(title,man_nodes['software category'], man_nodes, wbi))
    
    if(softwares['TITLE EXTRACTION']=={}):
        softwares['REPO NAME'].update(getEntitiesByName( name,man_nodes['software category'], man_nodes, wbi))
    
    
    softwares = softwares['REPO NAME'] | softwares['TITLE EXTRACTION']

    software_auto = [False, '']
    softwares_aux = None
    for i in softwares:
        if opt_nodes['code repository'] != []:
            if opt_nodes['code repository'] in softwares[i]['claims'].keys():
                for repo in softwares[i]['claims'][opt_nodes['code repository']]:
                    if repo['mainsnak']['datavalue']['value'] == info['code_repository'][0]['result']['value']:
                        softwares_aux = {i:softwares[i]}
                        software_auto = [True, 'URL match']  
                        break
    
   
    if softwares_aux != None:
        softwares = softwares_aux


    article_auto = [False, '']
    articles_aux = None
    
    for i in articles:

        if opt_nodes['DOI'] != []:
            if opt_nodes['DOI'] in articles[i]['claims'].keys():
                for doi in articles[i]['claims'][opt_nodes['DOI']]:
                    #print('DOI', doi)    
                    if doi['mainsnak']['datavalue']['value'] in DOIs.keys():
                        articles_aux = {i:articles[i]}
                        article_auto = [True, 'DOI match']
                        break

    if articles_aux != None:
        articles = articles_aux
    
    print("\n")
    click.echo(click.style('RESULTS', bold = True))
    if articles == {}:
        print('NO ARTICLES FOUND ON TARGET WIKIBASE')
    
    for i in articles.keys():
        print('ARTICLE FOUND: ',i, ' : ', articles[i]['labels']['en']['value'])

    if articles == {}:
        print('NO SOFTWARE FOUND ON TARGET WIKIBASE')
    for i in softwares.keys():
        print('SOFTWARE FOUND: ',i, ' : ', softwares[i]['labels']['en']['value'])


    

    
    
    article_links = {}
    software_links = {}

    for article in articles:
        
        #article_links[article] = getRelatedEntities( article, softwareQnode, mainSubjectPnode, instanceOfPnode, wbi)
        article_links[article] = getRelatedEntities(articles[article], softwares)
    
    for software in softwares:
        software_links[software] =  getRelatedEntities(softwares[software], articles)

    if article_links != {} or software_links !={}:
        print("\n")
        click.echo(click.style('CLASIFICATION', fg='red', bold = True))
        print("\n")
        click.echo(click.style('ENTITIES LINKED: ', bold=True))

    for i in article_links:
        for j in article_links[i]:
            print('ARTICLE [', i, ':', articles[i]['labels']['en']['value'], '] IS LINKED WITH SOFTWARE [', j[0], ':', j[1], '] THROUGH PROPERTY [', j[2],']')
    for i in software_links:
        for j in software_links[i]:
            print('SOFTWARE [', i, ':', softwares[i]['labels']['en']['value'], '] IS LINKED WITH ARTICLE [', j[0], ':', j[1], '] THROUGH PROPERTY [', j[2], ']')


    
    operation_list = SALTbotStatementDefiner.defineOperations(info, article_links, software_links,[auto, article_auto, software_auto], man_nodes, opt_nodes, results, wbi)
    
        
    return operation_list

        
        
    


    





  
