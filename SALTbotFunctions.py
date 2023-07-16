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

import time
import json


import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup


def getOptionalNodes(wbi):
    opt_nodes = {}

    
    query_license = ''' SELECT ?spdx ?item WHERE {?item wdt:P2479 ?spdx.}'''
    results = wbi_helpers.execute_sparql_query(query_license)
    licenses = {}
    for i in results['results']['bindings']:
        qnode_license = urlparse(i['item']['value']).path.replace("/", " ").split()[1]
        licenses.update({i['spdx']['value']:qnode_license})
    opt_nodes['licenses'] = licenses
    opt_nodes['code repository'] = wbi_helpers.search_entities(search_string='code repository', search_type='property')
    opt_nodes['programming language'] = wbi_helpers.search_entities(search_string='programming language', search_type='property')
    opt_nodes['download url'] = wbi_helpers.search_entities(search_string='download url', search_type='property')
    opt_nodes['license'] = wbi_helpers.search_entities(search_string='license', search_type='property')
    opt_nodes['version control system'] = wbi_helpers.search_entities(search_string='version control system', search_type='property')
    opt_nodes['web interface software'] = wbi_helpers.search_entities(search_string='web interface software', search_type='property')
    opt_nodes['Git'] = wbi_helpers.search_entities(search_string='Git', search_type='item')
    opt_nodes['GitHub'] = wbi_helpers.search_entities(search_string='GitHub', search_type='item')

    return opt_nodes
    

    
def getMandatoryNodes(wbi):
    prop_map = {}
    try:
        prop_map['instance of'] = wbi_helpers.search_entities(search_string='instance of', search_type='property')[0]	
        prop_map['main subject'] = wbi_helpers.search_entities(search_string='main subject', search_type='property')[0]	
        prop_map['described by source'] = wbi_helpers.search_entities(search_string='described by source', search_type='property')[0]
        prop_map['scholarly article'] = wbi_helpers.search_entities(search_string='scholarly article')[0]	
        prop_map['software category'] = wbi_helpers.search_entities(search_string='software category')[0]
        prop_map['free software'] = wbi_helpers.search_entities(search_string='free software')[0]
    except Exception as e:
        print('SALTbot Error: one or more of the required entities and properties has not been found in the target wikibase')
        print(e)
    
    return prop_map
#gets possible pnodes of target wikibase to create software pages and returns a list with all the possible statements for that software


def createSoftwareOperations(info, articleQnode, man_nodes, opt_nodes, wbi):
    resultOps = []
    #print(licenses)
    #Mandatory properties
    try:
        resultOps.append(['create',{'LABEL':info['name'][0]['result']['value'], 'DESCRIPTION':info['description'][0]['result']['value']}])
        resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':man_nodes['free software'], 'qualifiers':None}])
        #print('instanceof statement', ['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        
    except Exception as e:
        print(e)
    
    
    for prop in opt_nodes.keys():
        
        if opt_nodes[prop] != []:
            if prop == 'code repository':
                
                qualifiers = None
                if opt_nodes['web interface software']!=[] and opt_nodes['version control system']!=[] and opt_nodes['Git']!=[] and opt_nodes['GitHub'] !=[]:
                    qualifiers = Qualifiers()
                    qualifiers.add(Item(value=opt_nodes['Git'][0], prop_nr=opt_nodes['version control system'][0]))
                    qualifiers.add(Item(value=opt_nodes['GitHub'][0], prop_nr=opt_nodes['web interface software'][0]))
                resultOps.append(['statement',{'datatype':'URL', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop][0], 'o':info['code_repository'][0]['result']['value'], 'qualifiers':qualifiers}])
               
            if prop == 'programming language':
                dic_language = {}
                size = 0
                for language in info['programming_languages']:
                    
                    lang_name = language['result']['value']
                    lang_size = language['result']['size']

                    if lang_name == 'Jupyter Notebook':
                        lang_name = 'Python'
                    if lang_name in dic_language.keys():
                        dic_language.update({lang_name:dic_language[lang_name]+lang_size})

                    else:
                        dic_language.update({lang_name:lang_size})

                    size = size + lang_size
                for lang in dic_language:
                    if dic_language[lang]/size > 0.33:
                        try:
                            Qnode_programming_language = wbi_helpers.search_entities(search_string=lang)[0]
                            resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop][0], 'o':Qnode_programming_language, 'qualifiers':None}])
                        except:
                            continue
            if prop == 'license':
                for l in info['license']:
                    
                    try:
                        #print('spdx: ',l['result']['spdx_id'])
                        #print('keys: ', licenses.keys())
                        if l['result']['spdx_id'] in opt_nodes['licenses'].keys():
                            
                            resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop][0], 'o':opt_nodes['licenses'][l['result']['spdx_id']], 'qualifiers':None}])
                    except:
                        continue           
            if prop == 'download url':
                resultOps.append(['statement', {'datatype':'URL', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop][0], 'o':info['download_url'][0]['result']['value'], 'qualifiers':None}])
            #if prop == 'dateCreated':
            #    resultOps.append(['statement','Point in time' ['SOFTWARE', foundProps[prop][0], info['date_created'][0]['result']['value']]])
            #if prop == 'dateModified':
            #    resultOps.append(['statement', ['SOFTWARE', foundProps[prop][0], info['date_updated'][0]['result']['value']]])
            #if prop == 'license':
            #    resultOps.append(['statement', 'Item', ['SOFTWARE', foundProps[prop][0], info['license'][0]['result']['value']]])
            #except Exception as e:
            #    print(e)
    resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['described by source'], 'o':articleQnode, 'qualifiers':None}])
    #print(resultOps)
    return resultOps

#TODO:change to man_nodes
def defineOperations(info, article_links, software_links, man_nodes, opt_nodes, wbi):
    operation_list = []
    map_articles = {}
    map_softwares = {}


    if(article_links!={}):       
        click.echo(click.style('LINKING', fg='red', bold =True))
        count=1
        
        click.echo(click.style('SELECT AN ARTICLE : ', fg='blue', bold = True))
        print('0 : SKIP')
        map_articles.update({'0':'SKIP'})
        for i in article_links:
            print(count, ' : ', i)
            map_articles.update({str(count):i})
            count = count+1
           
        inp_article = input("ARTICLE NUMBER: ").strip()
        
        while(inp_article not in map_articles):
            inp_article = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()
        if inp_article == '0':
            return []
        if software_links !={}:
            count=1
            click.echo(click.style('SELECT A SOFTWARE : ', fg='blue', bold = True))
            print('0 : SKIP')
            map_softwares.update({'0':'SKIP'})
            for i in software_links:
                print(count, ' : ', i)
                map_softwares.update({str(count):i})
                count = count+1
            
            inp_software = input("SOFTWARE NUMBER: ").strip()
        
            while(inp_software not in map_softwares):
                inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()
            if inp_software == '0':
                return []
            operation_list = getRelations(operation_list, article_links,software_links,map_articles[inp_article],map_softwares[inp_software],man_nodes, wbi)
        else:
            aux_ops = createSoftwareOperations(info,map_articles[inp_article], man_nodes, opt_nodes, wbi)
            for i in aux_ops:
                operation_list.append(i)
            operation_list.append(['statement', {'datatype':'Item', 's':map_articles[inp_article], 'p':man_nodes['main subject'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
            
            
    return operation_list

def createEmptySoftware(data, wbi):
    print('Creating software...')
    item_wb = wbi.item.new()
    item_wb.labels.set(language='en', value=data['LABEL'])
    item_wb.descriptions.set(language='en', value=data['DESCRIPTION'])
    item_wb = item_wb.write() 
    print('Software created as ', item_wb.id)
    
    return item_wb



def createStatement(data,last_software,info, wbi):
    try:
        if data['s']==info['name'][0]['result']['value']:
            data['s'] =  last_software.id
        elif data['o'] ==   info['name'][0]['result']['value']:
            data['o'] =  last_software.id
        
        item_wb = wbi.item.get(entity_id=data['s'])
        if data['datatype'] == 'Item':
            item_wb.claims.add(Item(value=data['o'], prop_nr=data['p'], qualifiers = data['qualifiers']))
        elif data['datatype'] == 'URL':
            item_wb.claims.add(URL(value=data['o'], prop_nr=data['p'], qualifiers = data['qualifiers']))
            #item_wb.claims.add(URL)
        item_wb.write()
        print('succesfully created statement: ', data)
    except Exception as e:
        print('statement ', data, 'could not be imported. Reason: ', e)


def uploadChanges(info, operation_list, wbi):
    last_software = None

    for operation in operation_list:    
        #print(operation)
        if operation[0]=='create':
            last_software = createEmptySoftware(operation[1], wbi)
           
        elif operation[0] == 'statement':
            createStatement(operation[1],last_software,info, wbi)

def getRelations(operation_list, article_links, software_links, Qnode_article, Qnode_software, man_nodes,  wbi):
    article_software_link = False
    software_article_link = False

    for software in article_links[Qnode_article]:
        if software[0] == Qnode_software:
            article_software_link = True
  

        #print('no enlace articulo-software')
    for article in software_links[Qnode_software]:
        if article[0] == Qnode_article:
            software_article_link = True
    
    if article_software_link == False:
        operation_list.append(['statement', {'datatype':'Item', 's': Qnode_article, 'p':man_nodes['main subject'], 'o':Qnode_software}])
    if software_article_link == False:
        operation_list.append(['statement', {'datatype':'Item', 's':Qnode_software, 'p':man_nodes['described by source'], 'o':Qnode_article}])

    return operation_list

#Returns all entities related to entityQnode of class targetClass in the given wikibase
def getRelatedEntities2(entityJSON, candidates, property=None): 
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
        query = '''ASK {wd:'''+i['id']+''' wdt:'''+man_nodes['instance of']+'''+ wd:'''+targetClass+'''}'''
        match = wbi_helpers.execute_sparql_query(query)

        if(str(match['boolean'])=='True' and i['id'] not in entities.keys()):
            entities.update({i['id']:wbi.item.get(entity_id=i['id']).get_json()})

    return(entities)
    

#returns all the article titles detected
#info: json extracted with somef
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
                            parsedtitle = parsedyaml['preferred-citation']['title']
                        else:
                            parsedtitle = parsedyaml["title"]
                        #print(parsedyaml['preferred-citation']['title'])
                        #print("yaml")
                        print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
                        parsedinfo.append(parsedtitle)
                    except Exception as e:
                        print(e)  
                        
                
    print('authors:', authors)
    return parsedinfo, authors

#info: json extracted with somef
#wbi: wbi object with all the graph related info
#articleQnode: the article Qnode in the target wikibase
#softwareQnode: the software Qnode in target wikibase
#instanceofPnode: the instance_of property pnode in target wikibase
#TODO: change operation printing format
def SALTbot(wbi, info, man_nodes, opt_nodes):

    print("\n")
    click.echo(click.style('SEARCH', fg='red', bold=True))
    print("\n")

    
    articles = {"TITLE EXTRACTION":{}, "REPO NAME":{}}
    softwares = {"TITLE EXTRACTION":{}, "REPO NAME":{}}

    parsedTitles = parseTitles(info)

    if(parsedTitles == []):
        print("NO DETECTED TITLES")
    else:   
        for title in parsedTitles:       
            articles['TITLE EXTRACTION'].update(getEntitiesByName(title,man_nodes['scholarly article'], man_nodes, wbi))
            softwares['TITLE EXTRACTION'].update(getEntitiesByName(title,man_nodes['software category'], man_nodes, wbi))
            
    name = info['name'][0]['result']['value']

    if(articles['TITLE EXTRACTION']=={}):
        articles['REPO NAME'].update(getEntitiesByName( name,man_nodes['scholarly article'], man_nodes, wbi))
    if(softwares['TITLE EXTRACTION']=={}):
        softwares['REPO NAME'].update(getEntitiesByName( name,man_nodes['software category'], man_nodes, wbi))
    

    articles = articles['REPO NAME'] | articles['TITLE EXTRACTION']
    softwares = softwares['REPO NAME'] | softwares['TITLE EXTRACTION']

    
    print("\n")
    click.echo(click.style('RESULTS', bold = True))

    for i in articles.keys():
        print('ARTICLE FOUND: ',i, ' : ', articles[i]['labels']['en']['value'])
    for i in softwares.keys():
        print('SOFTWARE FOUND: ',i, ' : ', softwares[i]['labels']['en']['value'])
      

    print("\n")
    click.echo(click.style('CLASIFICATION', fg='red', bold = True))
    print("\n")
    click.echo(click.style('ARTICLES LINKED WITH SOFTWARE: ', bold=True))

    article_links = {}
    software_links = {}

    for article in articles:
        
        #article_links[article] = getRelatedEntities( article, softwareQnode, mainSubjectPnode, instanceOfPnode, wbi)
        article_links[article] = getRelatedEntities2(articles[article], softwares)
    
    for software in softwares:
        software_links[software] =  getRelatedEntities2(softwares[software], articles)

    for i in article_links:
        for j in article_links[i]:
            print('ARTICLE [', i, ':', articles[i]['labels']['en']['value'], '] IS LINKED WITH SOFTWARE [', j[0], ':', j[1], '] THROUGH PROPERTY [', j[2],']')
    for i in software_links:
        for j in software_links[i]:
            print('SOFTWARE [', i, ':', softwares[i]['labels']['en']['value'], '] IS LINKED WITH ARTICLE [', j[0], ':', j[1], '] THROUGH PROPERTY [', j[2], ']')



    operation_list = defineOperations(info, article_links, software_links, man_nodes, opt_nodes, wbi)

        
    return operation_list

        
        
    


    





  
