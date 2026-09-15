from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
#from wikiintegrator import wbi_core
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.datatypes import ExternalID, Item, String, URL, Quantity, Property, CommonsMedia, GlobeCoordinate
from wikibaseintegrator.models import Qualifiers
from wikibaseintegrator.wbi_enums import ActionIfExists
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import re
import json
import ast

def createEmptyEntity(data, wbi):
    try:
        print('Creating entity...')
   
        item_wb = wbi.item.new()
        item_wb.labels.set(language='en', value=data['LABEL'])
        item_wb.descriptions.set(language='en', value=data['DESCRIPTION'])
        summary='created '+ data['LABEL']
        item_wb = item_wb.write(summary=summary) 
        print('Item created as ', item_wb.id)
        return item_wb
    except Exception as e:
        print('Create ',data,' could not be done. Reason: ', e)






def createStatement(data, created_entities, subject_map, wbi):
    try:

        # Resolve references to entities created during this execution
        if data['s'] in created_entities:
            data['s'] = created_entities[data['s']]

        if data['o'] in created_entities:
            data['o'] = created_entities[data['o']]

        print(
            'creating statement [',
            data['s'],
            ' ',
            data['p'],
            ' ',
            data['o'],
            ']'
        )

        if data['s'] not in subject_map.keys():
            item_wb = wbi.item.get(entity_id=data['s'])
            subject_map.update({
                item_wb.id: [item_wb, '']
            })

        if data['datatype'] == 'Item':
            subject_map[data['s']][0].claims.add(
                Item(
                    value=data['o'],
                    prop_nr=data['p']
                ),
                action_if_exists=ActionIfExists.FORCE_APPEND
            )

            subject_map[data['s']][1] = (
                subject_map[data['s']][1]
                + ' '
                + str(data['p'])
                + ':'
                + str(data['o'])
                + ' '
            )

        elif data['datatype'] == 'URL':
            subject_map[data['s']][0].claims.add(
                URL(
                    value=data['o'],
                    prop_nr=data['p'],
                    qualifiers=data['qualifiers']
                ),
                action_if_exists=ActionIfExists.FORCE_APPEND
            )

            subject_map[data['s']][1] = (
                subject_map[data['s']][1]
                + ' '
                + str(data['p'])
                + ':'
                + str(data['o'])
                + ' '
            )

        print(
            'succesfully created [',
            data['s'],
            ' ',
            data['p'],
            ' ',
            data['o'],
            ']'
        )

    except Exception as e:
        print(
            'statement ',
            data,
            'could not be imported. Reason: ',
            e
        )

def updateChanges(operation_list, wbi):
    created_entities = {}
    subject_map = {}

    if operation_list == []:
        print(
            'SALTbot did not detect any relevant statements to add to the graph'
        )

    for operation in operation_list:

        if operation[0] == 'create':
            item_wb = createEmptyEntity(operation[1], wbi)

            if item_wb is None:
                print(
                    'Entity could not be created:',
                    operation[1]['LABEL']
                )
                continue

            # Map temporary label -> real Wikidata QID
            created_entities[operation[1]['LABEL']] = item_wb.id

            subject_map.update({
                item_wb.id: [item_wb, '']
            })

            print(
                "created_entities:",
                created_entities
            )

            print(
                "subject_map:",
                subject_map
            )

        elif operation[0] == 'statement':
            createStatement(
                operation[1],
                created_entities,
                subject_map,
                wbi
            )

    for entity in subject_map.keys():

        try:
            summary = subject_map[entity][1]

            print(
                'summary: ',
                summary
            )

            subject_map[entity][0].write(
                summary=summary
            )

        except Exception as e:
            print(e)


def executeOperations(operation_list,auto,wbi):
    
    click.echo(click.style('SALTbot WILL INTRODUCE THESE STATEMENTS IN WIKIDATA', fg='red', bold = True))
    #print(operation_list)
    #operation = json.load(str(operation_list.readlines()))
    #print(operation)
    operation_list_aux = []
    for operation in operation_list:
        #print('operation en bucle', operation)
        operation_aux = ast.literal_eval(operation)
        operation_list_aux.append(operation_aux)
        #print('operation_aux', operation_aux)
        #print('op 1', operation_aux[1])
        #print(operation_aux[1].keys())
        if operation_aux[0] == 'create':
            print('CREATE ENTITY [', operation_aux[1]['LABEL'], '] WITH DESCRIPTION [', operation_aux[1]['DESCRIPTION'],']')
        if operation_aux[0] == 'statement':
            print('CREATE STATEMENT [', operation_aux[1]['s'],' ',operation_aux[1]['p'],' ',operation_aux[1]['o'],'] OF TYPE [', operation_aux[1]['datatype'], ' WITH QUALIFIERS ', operation_aux[1]['qualifiers'],']')
    
    if auto == True:
        updateChanges(operation_list_aux, wbi)
    else:
        confirmation = input("CONFIRM (Y/N): ").strip()
            
        while(confirmation != "Y" and confirmation != "N"):
            confirmation = input("ONLY Y OR N ARE VALID CONFIRMATION ANSWERS. CONFIRM (Y/N): ").strip()	
            
        if(confirmation == "Y"):
            updateChanges(operation_list_aux, wbi)

