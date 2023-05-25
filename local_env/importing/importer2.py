from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_helpers
from wikibaseintegrator.datatypes import ExternalID, Item, String, URL, Quantity, Property, CommonsMedia, GlobeCoordinate
import json
import os
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
import pandas as pd


def change_config_wd():
    wbi_config['MEDIAWIKI_API_URL'] = 'https://www.wikidata.org/w/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = 'https://query.wikidata.org/'
    wbi_config['WIKIBASE_URL'] = 'https://www.wikidata.org'
    
def change_config_wb():
    wbi_config['MEDIAWIKI_API_URL'] = 'http://localhost:80/api.php'
    wbi_config['SPARQL_ENDPOINT_URL'] = 'http://localhost:8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
    wbi_config['WIKIBASE_URL'] = 'http://localhost:80'
    
def import_empty_entity(Qnode_wd, wbi):
    change_config_wd()
    try:
        item_wd = wbi.item.get(entity_id=Qnode_wd)
        #print('Q wikidata: ', item_wd.get_json()['labels']['en']['value'])
        item_wd_js = item_wd.get_json()
        
        change_config_wb()
        Qnode_wb=wbi_helpers.search_entities(item_wd_js['labels']['en']['value'])
            #print('Q wikibase: ', Qnode_wb)
            
        if Qnode_wb==[]:
            item_wb = wbi.item.new()
            data=[]
            print(Qnode_wd, 'not found in wikibase. Creating...')
                
                #Assign the same label it has on wikidata
            for lang in item_wd_js['labels'].keys():
                if lang == 'es' or lang == 'en':
                    item_wb.labels.set(language=lang, value=item_wd_js['labels'][lang]['value'])
                
                #print(item_wd_js['descriptions']['es'])
                
            for lang in item_wd_js['descriptions'].keys():
                if lang == 'es' or lang == 'en':
                    item_wb.descriptions.set(language=lang, value=item_wd_js['descriptions'][lang]['value'])
                
                    
            item_wb = item_wb.write()
            return item_wb.id
                
        elif len(Qnode_wb)>=1:
            print(Qnode_wd, 'found as ',Qnode_wb[0])
            return Qnode_wb[0]
        else:
            return None
         
    except Exception as e:
        print('failed to import: ', Qnode_wd, 'reason:', e)
        return None       
    
def import_property(Pnode_wd, wbi):
    try:
        change_config_wd()
        prop_wd = wbi.property.get(entity_id=Pnode_wd)
        prop_wd_js = prop_wd.get_json()




        change_config_wb()
        prop_wb = wbi_helpers.search_entities(search_string=prop_wd_js['labels']['en']['value'], search_type='property')

        if prop_wb == []:
            print(prop_wd.id, 'not found in wikibase. Creating...')
            prop_wb = wbi.property.new(datatype=prop_wd_js['datatype'])

            for lang in prop_wd_js['labels'].keys():
                if lang == 'es' or lang == 'en':
                    prop_wb.labels.set(language=lang, value=prop_wd_js['labels'][lang]['value'])

            for lang in prop_wd_js['descriptions'].keys():
                if lang == 'es' or lang == 'en':
                    prop_wb.descriptions.set(language=lang, value=prop_wd_js['descriptions'][lang]['value'])


            prop_wb = prop_wb.write()

            return prop_wb.id
        
        elif len(prop_wb)>=1:
            print(prop_wd.id, ' found as ', prop_wb[0])
            return prop_wb[0]
        else:
            return None
                #return create_prop(wbi)
    except Exception as e:
        print("failed to import: ", Pnode_wd," reason: ", e)
        return None
    
def import_statements(Qnode_wd, wbi):
    Qnode_wb = import_empty_entity(Qnode_wd, wbi)
    
    print(Qnode_wb)
    change_config_wd()
    item_wd = wbi.item.get(entity_id=Qnode_wd)
    item_wd_js = item_wd.get_json()
    
    change_config_wb()
    item_wb = wbi.item.get(entity_id=Qnode_wb)
    item_wb_js = item_wb.get_json()
    

    count=0
    
    data = []
    failed_statements = []
    for prop in item_wd_js['claims'].keys():
        try:
            P_node_property_wb = import_property(prop, wbi)
        except Exception as e:
            print("property ", prop, "could not be imported. Reason: ", e)
            continue
        for statement in item_wd_js['claims'][prop]:
            
            if statement['mainsnak']['datatype'] == "wikibase-item":
                
                
                try:
                    Q_node_value_wb = import_empty_entity(statement['mainsnak']['datavalue']['value']['id'], wbi)              
                        
                except:
                    Q_node_value_wb = None
                    
                if Q_node_value_wb != None and P_node_property_wb != None:
                    data.append(Item(value=Q_node_value_wb, prop_nr=P_node_property_wb))
                #print('ITEM', statement['mainsnak']['datavalue']['value']['id'])

            elif statement['mainsnak']['datatype'] == 'string':  
                if P_node_property_wb != None:          
                    data.append(String(value=statement['mainsnak']['datavalue']['value'], prop_nr=P_node_property_wb))
                #print('STRING', statement['mainsnak']['datavalue']['value'])

            elif statement['mainsnak']['datatype'] == 'external-id':
                if P_node_property_wb != None:              
                    data.append(ExternalID(value=statement['mainsnak']['datavalue']['value'], prop_nr=P_node_property_wb))
                #print('EX-ID', statement['mainsnak']['datavalue'])

            # elif statement['mainsnak']['datatype'] == 'url':
            #    true=1
            #    print(statement['mainsnak'])
            #    data.append(URL(value=statement['mainsnak']['datavalue']['value'], prop_nr='P4'))
                #print('URL ',statement['mainsnak']['datavalue']['value'])


            elif statement['mainsnak']['datatype'] == 'property':
                try:
                    P_node_imported = import_property(statement['mainsnak']['datavalue']['value'], wbi)
                    data.append(Property(value=P_node_imported, prop_nr=P_node_property_wb))
                except Exception as e:
                    print("property ", prop, "could not be imported. Reason: ", e)
                
                #data.append(Property(value=statement['mainsnak']['datavalue']['value'], prop_nr='P1'))
                #print('PROP ', statement['mainsnak']['datavalue'])
    
            elif statement['mainsnak']['datatype'] == 'globe-coordinate': 
            
                coord = statement['mainsnak']['datavalue']['value']
                if P_node_property_wb != None:  
                    data.append(GlobeCoordinate(latitude=coord['latitude'], longitude=coord['longitude'], altitude=coord['altitude'], precision=coord['precision'], globe=coord['globe'], prop_nr='P6'))
                #print('COORD ', statement['mainsnak']['datavalue'])
            try:
                item_wb.claims.add(data)
                item_wb.write()
            except Exception as e:
                failed_statements.append(statement)
            finally:
                data=[]
    #print(failed_statements)


@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    print("A3media wikibase importer")

@click.command()
@optgroup.group('Input', cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option('--file', '-f', type = click.Path(exists=True), help = 'Ruta para el fichero csv con Qnodos de wikidata a importar')

def main(file):
#Change these to a valid username and password on your local wikibase
    wikibase_user="User"
    wikibase_pwd="userpass1234"

    change_config_wb()
#change the USER_AGENT config parameter to edit the User-Agent header. See https://www.wikidata.org/wiki/Wikidata:Data_access for more info
    wbi_config['USER_AGENT'] = 'MyWikibaseBot/1.0 (http://localhost/wiki/User:User)'

#change username and password to your own account login data on Wikidata
    wb_login_instance = wbi_login.Clientlogin(user=wikibase_user, password=wikibase_pwd)

    wbi = WikibaseIntegrator(login=wb_login_instance)

    df = pd.read_csv(file)

    for i in df.iloc[:,0]:
        print('Importing ', i)
        try:
            import_statements(i, wbi)
        except:
            print('Failed to import ', i)

if(__name__=='__main__'):
	main()
