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

import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup

def createSoftwareOperations(info, man_nodes, opt_nodes, wbi):
    resultOps = []
    #print(licenses)
    #Mandatory properties
    try:
        resultOps.append(['create',{'LABEL':info['name'][0]['result']['value'], 'DESCRIPTION':info['description'][0]['result']['value']}])
        #print('instanceof statement', ['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':man_nodes['article'], 'qualifiers':None}])
    except Exception as e:
        print(e)

    print   
    
    free = False
    free_licenses = ["ZPL-2.1", "ZPL-2.0", "Zlib", "Zimbra-1.3", "Zend-2.0", "YPL-1.1", "xinetd", "XFree86-1.1", "X11",
    "WTFPL", "W3C", "Vim", "UPL-1.0", "Unlicense", "SPL-1.0", "SMLNJ", "Sleepycat", "SISSL", "SGI-B-2.0",
    "Ruby", "RPSL-1.0", "QPL-1.0", "Python-2.0", "PHP-3.01", "OSL-3.0", "OSL-2.1", "OSL-2.0", "OSL-1.1",
    "OSL-1.0", "OpenSSL", "OLDAP-2.7", "OLDAP-2.3", "OFL-1.1", "OFL-1.0", "ODbL-1.0", "NPL-1.1", "NPL-1.0",
    "NOSL", "Nokia", "NCSA", "MS-RL", "MS-PL", "MPL-2.0", "MPL-1.1", "MIT", "LPPL-1.3a", "LPPL-1.2",
    "LPL-1.02", "LGPL-3.0-or-later", "LGPL-3.0-only", "LGPL-2.1-or-later", "LGPL-2.1-only", "ISC",
    "IPL-1.0", "IPA", "Intel", "Imlib2", "iMatix", "IJG", "HPND", "GPL-3.0-or-later", "GPL-3.0-only",
    "GPL-2.0-or-later", "GPL-2.0-only", "gnuplot", "GFDL-1.3-or-later", "GFDL-1.3-only", "GFDL-1.2-or-later",
    "GFDL-1.2-only", "GFDL-1.1-or-later", "GFDL-1.1-only", "FTL", "FSFAP", "EUPL-1.2", "EUPL-1.1",
    "EUDatagrid", "EPL-2.0", "EPL-1.0", "EFL-2.0", "ECL-2.0", "CPL-1.0", "CPAL-1.0", "Condor-1.1",
    "ClArtistic", "CECILL-C", "CECILL-B", "CECILL-2.0", "CDDL-1.0", "CC0-1.0", "CC-BY-SA-4.0", "CC-BY-4.0",
    "BSL-1.0", "BSD-4-Clause", "BSD-3-Clause-Clear", "BSD-3-Clause", "BSD-2-Clause", "BitTorrent-1.1",
    "Artistic-2.0", "APSL-2.0", "Apache-2.0", "Apache-1.1", "Apache-1.0", "AGPL-3.0-or-later",
    "AGPL-3.0-only", "AFL-3.0", "AFL-2.1", "AFL-2.0", "AFL-1.2", "AFL-1.1"]

    for prop in opt_nodes.keys():
        qualifiers = None
        if opt_nodes[prop] != None:
            if prop == 'code repository':
                
                qualifiers = []
                if opt_nodes['web interface software']!=None and opt_nodes['version control system']!=None and opt_nodes['Git']!=None and opt_nodes['GitHub'] !=None:

                    qualifiers.append([opt_nodes['Git'], opt_nodes['version control system']])
                    qualifiers.append([opt_nodes['GitHub'], opt_nodes['web interface software']])

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
                        
                        if l['result']['spdx_id'] in free_licenses:
                            free = True
                    
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
    try:
        #qualifiers = Qualifiers()
        if opt_nodes['free software'] != None and free == True:
            resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':opt_nodes['free software'], 'qualifiers':qualifiers}])
        else:
            resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':man_nodes['software'], 'qualifiers':qualifiers}])
    except Exception as e:
        print(e)
    #qualifiers = Qualifiers()
    #resultOps.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['described by source'], 'o':articleQnode, 'qualifiers':qualifiers}])
    #print(resultOps)
    return resultOps

def createArticleOperations(info, man_nodes, opt_nodes, openAlex, wbi):
    resultOps = []
    #print(licenses)
    #Mandatory properties
    print(man_nodes)
    print(openAlex.keys())
    #resultOps.append(['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['instance of'], 'o':man_nodes['article'], 'qualifiers':None}])
   
    try:
        resultOps.append(['create',{'LABEL':openAlex['title'], 'DESCRIPTION':info['description'][0]['result']['value']}])
        #print('instanceof statement', ['statement',{'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':instanceOfPnode, 'o':softwareQnode[0]}])
        resultOps.append(['statement',{'datatype':'Item', 's':openAlex['title'], 'p':man_nodes['instance of'], 'o':man_nodes['scholarly article'], 'qualifiers':None}])
    except Exception as e:
        print(e)
    
    for prop in opt_nodes.keys():
        qualifiers = None
        if opt_nodes[prop] != None:
            if prop == 'DOI':
                if 'doi' in openAlex.keys():
                    resultOps.append(['statement',{'datatype':'Item', 's':openAlex['title'], 'p':opt_nodes['DOI'], 'o':openAlex['doi'], 'qualifiers':None}])
            if prop == 'OpenAlex ID':
                if 'id' in openAlex.keys():
                    resultOps.append(['statement',{'datatype':'Item', 's':openAlex['title'], 'p':opt_nodes['OpenAlex ID'], 'o':openAlex['id'], 'qualifiers':None}])
    return resultOps

#TODO:change to man_nodes
def defineOperations(info, article_links, software_links,auto, man_nodes, opt_nodes, results, openAlex, wbi):
    operation_list = []
    map_articles = {}
    map_softwares = {}

    #print(man_nodes)
    #print(opt_nodes)
    #print('article links: ', article_links)
    #print('software links: ', software_links)


    
           
    count=1
    click.echo(click.style('LINKING', fg='red', bold =True))
    qnode_article = None
    qnode_software = None
    
    #TODO:Si no hay articulos lo crea
    if article_links == {}:
        aux_ops = createArticleOperations(info, man_nodes, opt_nodes, openAlex, wbi)
        for i in aux_ops:
                operation_list.append(i)
    #SI HAY ARTICULOS
    else:
        #SELECCION ARTICULO
        click.echo(click.style('SELECT AN ARTICLE : ', fg='blue', bold = True))
        print('0 : CREATE ARTICLE')
        map_articles.update({'0':'SKIP'})
        count = 1
        for i in article_links:
            print(count, ' : ', i)
            map_articles.update({str(count):i})
            count = count+1

        inp_article = input("ARTICLE NUMBER: ").strip()
        while(inp_article not in map_articles):
            inp_article = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()
        
        #SI SELECCIONA 0, crear
        if inp_article == '0':
                #results[info['code_repository'][0]['result']['value']].update({'software':software_links.keys()})
                #return []
            aux_ops = createArticleOperations(info, man_nodes, opt_nodes,openAlex, wbi)
            #    qnode_article = info['name'][0]['result']['value'] + ' scholarly article'
            for i in aux_ops:
                operation_list.append(i)
        #SI SELECCIONA OTRO, GUARAR QNODO
        else:
            qnode_article = map_articles[inp_article]
            #results[info['code_repository'][0]['result']['value']].update({'article':map_articles[inp_article]})
  
    '''            
    if article_links !={}:
        click.echo(click.style('SELECT AN ARTICLE : ', fg='blue', bold = True))
        print('0 : SKIP')
        map_articles.update({'0':'SKIP'})
        for i in article_links:
            print(count, ' : ', i)
            map_articles.update({str(count):i})
            count = count+1
       
    
        if auto[0] == True and auto[1][0]==True:
            qnode_article = map_articles[inp_article]
            print('AUTOMATICALLY SELECTED ', map_articles[inp_article], 'AS ARTICLE DUE TO', auto[1][1])
            results[info['code_repository'][0]['result']['value']].update({'article':qnode_article})
        else:
            inp_article = input("ARTICLE NUMBER: ").strip()
            while(inp_article not in map_articles):
                inp_article = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()
            if inp_article == '0':
                results[info['code_repository'][0]['result']['value']].update({'software':software_links.keys()})
                #return []
                aux_ops = createArticleOperations(info, man_nodes, opt_nodes, wbi)
                qnode_article = info['name'][0]['result']['value'] + ' scholarly article'
                for i in aux_ops:
                    operation_list.append(i)
            else:
                qnode_article = map_articles[inp_article]
                results[info['code_repository'][0]['result']['value']].update({'article':map_articles[inp_article]})
    else:
        aux_ops = createArticleOperations(info, man_nodes, opt_nodes, wbi)
        qnode_article = info['name'][0]['result']['value'] + ' scholarly article'
        for i in aux_ops:
            operation_list.append(i)
        #operation_list.append(['statement', {'datatype':'Item', 's':map_softwares[inp_article], 'p':man_nodes['described by source'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
    #print(operation_list)
    '''
    #print('inp_article: ', inp_article)
    #SI NO HAY SOFTWARE SE CREA
    if software_links == {}:
        aux_ops = createSoftwareOperations(info, man_nodes, opt_nodes, wbi)
        for i in aux_ops:
            operation_list.append(i)
    #SI HAY SOFTWARE
    else:
        #SELECCIONAR SOFTWARE
        click.echo(click.style('SELECT A SOFTWARE : ', fg='blue', bold = True))
        print('0 : CREATE SOFTWARE')
        count = 1
        map_softwares.update({'0':'SKIP'})
        for i in software_links:
            print(count, ' : ', i)
            map_softwares.update({str(count):i})
            count = count+1
        inp_software = input("SOFTWARE NUMBER: ").strip()
    
        while(inp_software not in map_softwares):
            inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()   
        
        #SI NO SE SELCCIONA SE CREA     
        if inp_software == '0':
            aux_ops = createSoftwareOperations(info, man_nodes, opt_nodes, wbi)
            for i in aux_ops:
                operation_list.append(i)
        else:
            qnode_software = map_softwares[inp_software]
    
    #check enlaces
    if qnode_article == None or qnode_software == None:
        
        operation_list.append(['statement', {'datatype':'Item', 's':str(info['name'][0]['result']['value'])+' scholarly article', 'p':man_nodes['main subject'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
        operation_list.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['described by source'], 'o':str(info['name'][0]['result']['value'])+' scholarly article', 'qualifiers':None}])

    else:
       getRelations(operation_list, article_links, software_links, qnode_article, qnode_software,man_nodes, results, wbi) 
    '''if software_links !={}:
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
        #elif len(article_links[map_articles[inp_article]]) == 1:
        #    for i in map_softwares:
                
        #        if map_softwares[i]==article_links[map_articles[inp_article]][0][0]:    
        #            inp_software = i
        #            print('AUTOMATICALLY SELECTED ', map_softwares[inp_software], 'AS SOFTWARE DUE TO PREVIOUS LINK WITH', map_articles[inp_article])
        #            results[info['code_repository'][0]['result']['value']].update({'software':map_softwares[inp_software]})
        else:
            inp_software = input("SOFTWARE NUMBER: ").strip()
    
            while(inp_software not in map_softwares):
                inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()
            #if inp_software == '0':
            #    return []
            else:
                results[info['code_repository'][0]['result']['value']].update({'software':map_softwares[inp_software]})
        if article_links != {} and inp_article != '0':
            operation_list = getRelations(operation_list, article_links,software_links,qnode_article,map_softwares[inp_software],man_nodes, results[info['code_repository'][0]['result']['value']], wbi)
        else:
            operation_list.append(['statement', {'datatype':'Item', 's':qnode_article, 'p':man_nodes['main subject'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
            operation_list.append(['statement', {'datatype':'Item', 's':info['name'][0]['result']['value'], 'p':man_nodes['described by source'], 'o':qnode_article}])

    else:
        aux_ops = createSoftwareOperations(info,qnode_article, man_nodes, opt_nodes, wbi)
        for i in aux_ops:
            operation_list.append(i)
        operation_list.append(['statement', {'datatype':'Item', 's':qnode_article, 'p':man_nodes['main subject'], 'o':info['name'][0]['result']['value'], 'qualifiers':None}])
    '''    
    #prnt('results en operations', results)
    #print('operation list en operations', operation_list)
    for i in operation_list:
        print(i)
    return operation_list


#TODO: Move to searcher
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
    #print('operation list in get relations', operation_list)
    return operation_list