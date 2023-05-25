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


import time
import json


import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

#gets possible pnodes of target wikibase to create software pages and returns a list with all the possible statements for that software

#TODO: some of the properties are not correctly detected
def createSoftwareOperations(info, instanceOfPnode, describedBySourcePnode, articleQnode, wbi):
    foundProps = {}
    resultOps = []

    #Mandatory properties
    try:
        resultOps.append(['create',{'LABEL':info['name'][0]['result']['value'], 'DESCRIPTION':info['description'][0]['result']['value']}])
        softwareQnode = wbi_helpers.search_entities(search_string='free software')
        resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        print('instanceof statement', ['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        
    except Exception as e:
        print(e)
    
    #Optional properties
    foundProps['codeRepository'] = wbi_helpers.search_entities(search_string='codeRepository', search_type='property')
    foundProps['programmingLanguage'] = wbi_helpers.search_entities(search_string='programmingLanguage', search_type='property')
    foundProps['downloadUrl'] = wbi_helpers.search_entities(search_string='downloadUrl', search_type='property')
    #foundProps['dateCreated'] = wbi_helpers.search_entities(search_string='dateCreated', search_type='property')
    #foundProps['dateModified'] = wbi_helpers.search_entities(search_string='dateModified', search_type='property')
    foundProps['license'] = wbi_helpers.search_entities(search_string='license', search_type='property')

    print(foundProps)

    for prop in foundProps.keys():
        if foundProps[prop] != []:
            if prop == 'codeRepository':
                resultOps.append(['statement',{'datatype':'URL', 's':info['name']['0']['result']['value'], 'p':foundProps[prop[0]], 'o':info['codeRepository']['0']['result']['value']}])
               
            if prop == 'programmingLanguage':
                for language in info['programming_languages']:
                    resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':foundProps[prop][0], 'o':language['value']}])
            if prop == 'downloadUrl':
                resultOps.append(['statement', {'datatype':'URL', 's':info['name'][0]['result']['value'], 'p':foundProps[prop][0], 'o':info['download_url'][0]['result']['value']}])
            #if prop == 'dateCreated':
            #    resultOps.append(['statement','Point in time' ['SOFTWARE', foundProps[prop][0], info['date_created'][0]['result']['value']]])
            #if prop == 'dateModified':
            #    resultOps.append(['statement', ['SOFTWARE', foundProps[prop][0], info['date_updated'][0]['result']['value']]])
            #if prop == 'license':
            #    resultOps.append(['statement', 'Item', ['SOFTWARE', foundProps[prop][0], info['license'][0]['result']['value']]])
            #except Exception as e:
            #    print(e)
    resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':describedBySourcePnode, 'o':articleQnode}])
    #print(resultOps)
    return resultOps

#TODO:write documentation
#TODO: mainsubject software and describedBySource article statements are always added -> check if the bug is here
def defineOperations(info, article_links, software_links, mainSubjectPnode, describedBySourcePnode, instanceOfPnode, wbi):
    operation_list = []
    map_articles = {}
    map_softwares = {}

    if(article_links!={}):       
        click.echo(click.style('LINKING', fg='red', bold =True))
        count=0
        
        click.echo(click.style('SELECT AN ARTICLE : ', fg='blue', bold = True))
        for i in article_links:
            print(count, ' : ', i)
            map_articles.update({str(count):i})
            count = count+1
           
        inp_article = input("ARTICLE NUMBER: ").strip()
        
        while(inp_article not in map_articles):
            inp_article = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()
        
        if software_links !={}:
            count=0
            click.echo(click.style('SELECT A SOFTWARE : ', fg='blue', bold = True))
            for i in software_links:
                print(count, ' : ', i)
                map_softwares.update({str(count):i})
                count = count+1
            
            inp_software = input("SOFTWARE NUMBER: ").strip()
        
            while(inp_software not in map_softwares):
                inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()
            operation_list = getRelations(operation_list, article_links,software_links,map_articles[inp_article],map_softwares[inp_software], mainSubjectPnode, describedBySourcePnode, wbi)
        else:
            aux_ops = createSoftwareOperations(info, instanceOfPnode, describedBySourcePnode, map_articles[inp_article], wbi)
            for i in aux_ops:
                operation_list.append(i)
            operation_list.append(['statement', {'datatype':'Item', 's':map_articles[inp_article], 'p':mainSubjectPnode, 'o':info['name'][0]['result']['value']}])
            
            
    return operation_list

#TODO: write documentation
#TODO: do the software existance comprobation before calling this function
def createEmptySoftware(data, wbi):
    item_wb = None
    try:
        item_qnode = wbi_helpers.search_entities(search_string=data['LABEL'], search_type='item')[0]
        item_wb = wbi.item.get(entity_id=item_qnode)
    except:
        print('Creating software...')
        item_wb = wbi.item.new()
        item_wb.labels.set(language='en', value=data['LABEL'])
        item_wb.descriptions.set(language='en', value=data['DESCRIPTION'])
        item_wb = item_wb.write() 
        print('Software created as ', item_wb.id)
    
    return item_wb


#TODO: write documentation
#TODO: change the entity search for every statement
#TODO: only works with statements of type Item -> needs to be working for URL and date as well
def createStatement(data, wbi):
    try:
        if data['s'][0]!='Q':
            data['s'] =  wbi_helpers.search_entities(search_string=data['s'], search_type='item')[0]
        elif data['o'][0]!='Q':    
            data['o'] =  wbi_helpers.search_entities(search_string=data['o'], search_type='item')[0]
        print('data after createStatements', data)
        item_wb = wbi.item.get(entity_id=data['s'])
        statement_data = []
        statement_data.append(Item(value=data['o'], prop_nr=data['p']))
        item_wb.claims.add(statement_data)
        item_wb.write()
    except Exception as e:
        print('statement ', data, 'could not be imported. Reason: ', e)

#TODO:write documentation
#TODO: check if software operations are created correctly    
def uploadChanges(info, operation_list, wbi):
    for operation in operation_list:
        #print(operation)
        if operation[0]=='create':
            createEmptySoftware(operation[1], wbi)
           
        elif operation[0] == 'statement':
            createStatement(operation[1], wbi)

#TODO:write documentation
#TODO:check if statements are detected correctly here
def getRelations(operation_list, article_links, software_links, Qnode_article, Qnode_software, mainSubjectPnode, describedBySourcePnode,  wbi):
    
    if Qnode_software not in article_links[Qnode_article]:
        #if software == Qnode_software:
        operation_list.append(['statement', {'datatype':'Item', 's': Qnode_article, 'p':mainSubjectPnode, 'o':Qnode_software}])

        #print('no enlace articulo-software')
    if Qnode_article not in software_links[Qnode_software]:
        operation_list.append(['statement', {'datatype':'Item', 's':Qnode_software, 'p':describedBySourcePnode, 'o':Qnode_article}])
    
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
def getEntitiesByName(name, targetClass, instanceOf, wbi):

    entities={}

    results_wbi_helper = wbi_helpers.search_entities(search_string=name, dict_result=True, search_type='item')

    for i in results_wbi_helper:      
        query = '''ASK {wd:'''+i['id']+''' wdt:'''+instanceOf+'''+ wd:'''+targetClass+'''}'''
        match = wbi_helpers.execute_sparql_query(query)

        if(str(match['boolean'])=='True' and i['id'] not in entities.keys()):
            entities.update({i['id']:wbi.item.get(entity_id=i['id']).get_json()})

    return(entities)
    

#info: json extracted with somef
#returns all the article titles detected
#TODO: change try catch workflow
def parseTitles(info):
    parsedinfo = []

    # For each extraction technique
    for i in info["citation"]:


        #If it is File Exploration or Regular expression
        if(i["technique"] == "file_exploration" or i["technique"] == "regular_expression"):
            
        
            #try parsing to BIB
            try:
                parsedbib= bibtexparser.loads(i["result"]["value"])
                parsedtitle = parsedbib.entries[0]["title"]
                print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
                parsedinfo.append(parsedtitle)
            except Exception as e:
                #print(e)
            #try parsing to YAML
            
                try:
                    parsedyaml = yaml.load(i["result"]["value"], Loader = SafeLoader)
                    #print(parsedyaml.keys())
                    if('preferred-citation' in parsedyaml.keys()):
                        parsedtitle = parsedyaml['preferred-citation']['title']
                    else:
                        parsedtitle = parsedyaml["title"]
                    #print(parsedyaml['preferred-citation']['title'])
                    #print("yaml")
                    print("DETECTED TITLE: ", parsedtitle, "     ", "TECHNIQUE: ", i["technique"])
                    parsedinfo.append(parsedtitle)
                except Exception as e:
                    print(e)  
                    
                

    return parsedinfo

#info: json extracted with somef, wbi: wbi object, 
#articleQnode: the article Qnode in the target wikibase, 
#softwareQnode: the software Qnode in target wikibase, 
#instanceofPnode: the instance_of property pnode in target wikibase
#TODO: change operation printing format
def SALTbot(info, wbi, articleQnode, softwareQnode, instanceOfPnode, subclassOfPnode, mainSubjectPnode, describedBySourcePnode):

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
            articles['TITLE EXTRACTION'].update(getEntitiesByName( title, articleQnode, instanceOfPnode, wbi))
            softwares['TITLE EXTRACTION'].update(getEntitiesByName(title, softwareQnode, instanceOfPnode, wbi))
            
    name = info['name'][0]['result']['value']

    if(articles['TITLE EXTRACTION']=={}):
        articles['REPO NAME'].update(getEntitiesByName( name, articleQnode, instanceOfPnode, wbi))
    if(softwares['TITLE EXTRACTION']=={}):
        softwares['REPO NAME'].update(getEntitiesByName( name, softwareQnode, instanceOfPnode, wbi))
    

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


    operation_list = defineOperations(info, article_links, software_links, mainSubjectPnode, describedBySourcePnode, instanceOfPnode, wbi)

        
    return operation_list

        
        
    


    





  
