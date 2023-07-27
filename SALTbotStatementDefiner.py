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

def createSoftwareOperations(info, articleQnode, man_nodes, opt_nodes, wbi):
    resultOps = []
    #print(licenses)
    #Mandatory properties
    try:
        resultOps.append(['create',{'LABEL':info['name'][0]['result']['value'], 'DESCRIPTION':info['description'][0]['result']['value']}])
        qualifiers = Qualifiers()
        resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':man_nodes['free software'], 'qualifiers':qualifiers}])
        #print('instanceof statement', ['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        
    except Exception as e:
        print(e)
    
    
    for prop in opt_nodes.keys():
        qualifiers = Qualifiers()
        if opt_nodes[prop] != None:
            if prop == 'code repository':
                
                qualifiers = Qualifiers()
                if opt_nodes['web interface software']!=None and opt_nodes['version control system']!=None and opt_nodes['Git']!=None and opt_nodes['GitHub'] !=None:

                    qualifiers.add(Item(value=opt_nodes['Git'], prop_nr=opt_nodes['version control system']))
                    qualifiers.add(Item(value=opt_nodes['GitHub'], prop_nr=opt_nodes['web interface software']))

                resultOps.append(['statement',{'datatype':'URL', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop], 'o':info['code_repository'][0]['result']['value'], 'qualifiers':qualifiers}])
               
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
                            Qnode_programming_language = getCorrectQnode(lang, wbi_helpers.search_entities(search_string=lang, dict_result = True))
                            if Qnode_programming_language != None:
                                resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop], 'o':Qnode_programming_language, 'qualifiers':qualifiers}])
                        except:
                            continue
            if prop == 'license':
                for l in info['license']:
                    
                    try:
                        #print('spdx: ',l['result']['spdx_id'])
                        #print('keys: ', licenses.keys())
                        if l['result']['spdx_id'] in opt_nodes['licenses'].keys():
                            
                            resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop], 'o':opt_nodes['licenses'][l['result']['spdx_id']], 'qualifiers':qualifiers}])
                    except:
                        continue           
            if prop == 'download url':
                resultOps.append(['statement', {'datatype':'URL', 's':info['name'][0]['result']['value'], 'p':opt_nodes[prop], 'o':info['download_url'][0]['result']['value'], 'qualifiers':qualifiers}])
            #if prop == 'dateCreated':
            #    resultOps.append(['statement','Point in time' ['SOFTWARE', foundProps[prop][0], info['date_created'][0]['result']['value']]])
            #if prop == 'dateModified':
            #    resultOps.append(['statement', ['SOFTWARE', foundProps[prop][0], info['date_updated'][0]['result']['value']]])
            #if prop == 'license':
            #    resultOps.append(['statement', 'Item', ['SOFTWARE', foundProps[prop][0], info['license'][0]['result']['value']]])
            #except Exception as e:
            #    print(e)
    qualifiers = Qualifiers()
    resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['described by source'], 'o':articleQnode, 'qualifiers':qualifiers}])
    #print(resultOps)
    return resultOps

#TODO:change to man_nodes
def defineOperations(info, article_links, software_links,auto, man_nodes, opt_nodes, results, wbi):
    operation_list = []
    map_articles = {}
    map_softwares = {}

    #print('article links: ', article_links)
    #print('software links: ', software_links)


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
           
        
        if auto[0] == True and auto[1][0]==True:
            inp_article = '1'
            print('AUTOMATICALLY SELECTED ', map_articles[inp_article], 'AS ARTICLE DUE TO', auto[1][1])
            results[info['code_repository'][0]['result']['value']].update({'article':map_articles[inp_article]})
        else:
            inp_article = input("ARTICLE NUMBER: ").strip()
            while(inp_article not in map_articles):
                inp_article = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()
            if inp_article == '0':
                results[info['code_repository'][0]['result']['value']].update({'software':software_links.keys()})
                return []
            else:
                results[info['code_repository'][0]['result']['value']].update({'article':map_articles[inp_article]})
        if software_links !={}:
            count=1
            click.echo(click.style('SELECT A SOFTWARE : ', fg='blue', bold = True))
            print('0 : SKIP')
            map_softwares.update({'0':'SKIP'})
            for i in software_links:
                print(count, ' : ', i)
                map_softwares.update({str(count):i})
                count = count+1
            
            #print('auto: ',auto)
            if auto[0] == True and auto[2][0]==True:
                inp_software = '1'
                print('AUTOMATICALLY SELECTED ', map_softwares[inp_software], 'AS SOFTWARE DUE TO', auto[2][1])
                results[info['code_repository'][0]['result']['value']].update({'software':map_softwares[inp_software]})

            elif len(article_links[map_articles[inp_article]]) == 1:
                for i in map_softwares:
                    
                    if map_softwares[i]==article_links[map_articles[inp_article]][0][0]:    
                        inp_software = i
                        print('AUTOMATICALLY SELECTED ', map_softwares[inp_software], 'AS SOFTWARE DUE TO PREVIOUS LINK WITH', map_articles[inp_article])
                        results[info['code_repository'][0]['result']['value']].update({'software':map_softwares[inp_software]})
            else:
                inp_software = input("SOFTWARE NUMBER: ").strip()
        
                while(inp_software not in map_softwares):
                    inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()
                if inp_software == '0':
                    return []
                else:
                    results[info['code_repository'][0]['result']['value']].update({'software':map_softwares[inp_software]})

            operation_list = getRelations(operation_list, article_links,software_links,map_articles[inp_article],map_softwares[inp_software],man_nodes, results[info['code_repository'][0]['result']['value']], wbi)
        else:
            aux_ops = createSoftwareOperations(info,map_articles[inp_article], man_nodes, opt_nodes, wbi)
            for i in aux_ops:
                operation_list.append(i)
            operation_list.append(['statement', {'datatype':'Item', 's':map_articles[inp_article], 'p':man_nodes['main subject'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
            
    #print('results en operations', results)
    return operation_list


def getRelations(operation_list, article_links, software_links, Qnode_article, Qnode_software, man_nodes, results,  wbi):
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

    results['article-software-link'] = article_software_link
    results['software-article-link'] = software_article_link

    #print('results en get relations:', results)
    #print('operation list', operation_list)
    return operation_list