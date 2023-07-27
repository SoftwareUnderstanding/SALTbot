from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
#from wikiintegrator import wbi_core
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.datatypes import ExternalID, Item, String, URL, Quantity, Property, CommonsMedia, GlobeCoordinate
from wikibaseintegrator.models import Qualifiers
from wikibaseintegrator.wbi_enums import ActionIfExists
import pandas as pd
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import re


def createEmptySoftware(data, wbi):
    try:
        print('Creating software...')
   
        item_wb = wbi.item.new()
        item_wb.labels.set(language='en', value=data['LABEL'])
        item_wb.descriptions.set(language='en', value=data['DESCRIPTION'])
        item_wb = item_wb.write() 
        print('Software created as ', item_wb.id)
        return item_wb
    except Exception as e:
        print('Create ',data,' could not be done. Reason: ', e)


def createStatement(data,last_software,subject_map, wbi):
    try:
  
        if not re.search("Q\d+", data['s']):
            data['s'] =  last_software.id
        elif not re.search("Q\d+", data['o']):
            data['o'] =  last_software.id
        
        print('creating statement [', data['s'], ' ', data['p'],' ' ,data['o'], ']')

        if data['s'] not in subject_map.keys():
            item_wb = wbi.item.get(entity_id=data['s'])
            subject_map.update({item_wb.id:item_wb})
        if data['datatype'] == 'Item':
            subject_map[data['s']].claims.add(Item(value=data['o'], prop_nr=data['p']),action_if_exists = ActionIfExists.FORCE_APPEND)
        elif data['datatype'] == 'URL':
            subject_map[data['s']].claims.add(URL(value=data['o'], prop_nr=data['p'], qualifiers=data['qualifiers']), action_if_exists = ActionIfExists.FORCE_APPEND)
        print('succesfully created [', data['s'], ' ', data['p'],' ' ,data['o'], ']')
    except Exception as e:
        print('statement ', data, 'could not be imported. Reason: ', e)


def updateChanges(operation_list, wbi):
    last_software = None
    subject_map = {}
    if(operation_list == []):
        print('SALTbot did not detect any relevant statements to add to the graph')
    for operation in operation_list:    
        #print(operation)
        if operation[0]=='create':
            last_software = createEmptySoftware(operation[1], wbi)
            subject_map.update({last_software.id:last_software}) 
           
        elif operation[0] == 'statement':
            createStatement(operation[1],last_software,subject_map, wbi)
    for entity in subject_map.keys():
        subject_map[entity].write()



def executeOperations(operation_list,auto,wbi):
    
    click.echo(click.style('SALTbot WILL INTRODUCE THESE STATEMENTS IN WIKIDATA', fg='red', bold = True))
    for operation in operation_list:
        if operation[0] == 'create':
            print('CREATE SOFTWARE [', operation[1]['LABEL'], '] WITH DESCRIPTION [', operation[1]['DESCRIPTION'],']')
        if operation[0] == 'statement':
            print('CREATE STATEMENT [', operation[1]['s'],' ',operation[1]['p'],' ',operation[1]['o'],'] OF TYPE [', operation[1]['datatype'], ']')
    
    if auto != True:
        updateChanges(operation_list, wbi)
    else:
        confirmation = input("CONFIRM (Y/N): ").strip()
            
        while(confirmation != "Y" and confirmation != "N"):
            confirmation = input("ONLY Y OR N ARE VALID CONFIRMATION ANSWERS. CONFIRM (Y/N): ").strip()	
            
        if(confirmation == "Y"):
            updateChanges(operation_list, wbi)

