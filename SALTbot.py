#!/home/jorge/TFG/TFGenv/bin/python
import json
import os
import sys
from urllib.parse import urlparse

import yaml
from yaml.loader import SafeLoader

import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from datetime import datetime

import glob
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_helpers

import SALTbot2



@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    print("SALTbot: Software and Article Linker Toolbot")


@click.command()
@click.option('--auto', '-a', is_flag=True, help='Sets bot to auto mode. The bot will not ask for user confirmations and will only require supervision if one or more articles or software are found in Wikidata.')
@click.option('--keyword', '-k', default = None, help = 'Keyword for searching in case the repository treatment found no articles or software on Wikidata.')
@click.option('--output', '-o', default=None, type = click.Path(), help='If url is used, this will be the path of the metadata output produced by SOMEF.')




#TODO: change this from flag to command
@click.option('--target', is_flag=True, help='change the target wikibase instance')
@click.option('--login', is_flag=True, help='Change the username and password credentials in the target wikibase')

@optgroup.group('Input', cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option('--readmedir', '-rdir', type = click.Path(exists=True), help = 'Path to the target repository if the repository is local.')
@optgroup.option('--url', '-u', help = 'URL of the remote target repository.')
@optgroup.option('--urlfile','-ru', type = click.Path(exists=True), help='File with one or more url entries to be treated. SALTbot will analyze each individual url in succesion and introduce the links afterwards.')
@optgroup.option('--jsonfile','-js', type = click.Path(exists=True), help='Path to the JSON extracted from the target repository with SOMEF.')
@optgroup.option('--jsondir', '-rjs', type = click.Path(exists=True), help = 'Path of a directory with one or multiple JSONs extracted with SOMEF. SALTbot will analyze each individual json in succesion and introduce the links afterwards.')



#TODO: remove upload flag
#TODO: move target and login to config.yml
#TODO: reactivate options for massive treatment
def main(target, login, readmedir, jsonfile, url, urlfile, jsondir, auto, keyword,  output):

	#Local wikibase configuration. Uncomment these lines and edit them to target other wikibases

	#wbi_config['MEDIAWIKI_API_URL'] = 'http://localhost:80/api.php'
	#wbi_config['SPARQL_ENDPOINT_URL'] = 'http://localhost:8834/proxy/wdqs/bigdata/namespace/wdq/sparql'
	#wbi_config['WIKIBASE_URL'] = 'http://localhost:80'
	
	
	user = ''
	passw = '' 

	

	wbi_config['USER_AGENT'] = 'SALTbot/1.0 (https://www.wikidata.org/wiki/User:'+user+')'
	
	wbi_config['USER_AGENT'] = 'SALTbot/1.0 (https://www.wikidata.org/wiki/User:TrialAndError2)'
	
	wbi=WikibaseIntegrator(login=wbi_login.Clientlogin(user=user, password=passw))
	
	try:
		wb_subclassOf_Pnode = wbi_helpers.search_entities(search_string='subclass of', search_type='property')[0]
		print("subclass: ", wb_subclassOf_Pnode)
		wb_instanceOf_Pnode = wbi_helpers.search_entities(search_string='instance of', search_type='property')[0]
		print("instance: ",wb_instanceOf_Pnode)
		wb_mainSubject_Pnode = wbi_helpers.search_entities(search_string='main subject', search_type='property')[0]
		print("main subject: ", wb_mainSubject_Pnode)
		wb_describedBySource_Pnode = wbi_helpers.search_entities(search_string='described by source', search_type='property')[0]
		print("described by source: ",wb_describedBySource_Pnode)
		wb_article_Qnode = wbi_helpers.search_entities(search_string='scholarly article')[0]
		print("article: ", wb_article_Qnode)
		wb_software_Qnode = wbi_helpers.search_entities(search_string='software category')[0]
		print("software: ", wb_software_Qnode)

	except Exception as e:
		print('SALTbot Error: one or more of the required entities and properties has not been found in the target wikibase')
		print(e)
		return

	
	
	
	
	
	
	#Change this to true if you wish to edit wikidata
	upload = True

	operation_list = []

	#TODO: move to config yaml
	if(target):
		wbi_config['MEDIAWIKI_API_URL'] = input("Introduce target's Mediawiki API URL: ").strip()
		wbi_config['SPARQL_ENDPOINT_URL'] = input("Introduce target's SPARQL Endpoint URL: ").strip()
		wbi_config['WIKIBASE_URL'] = input("Introduce target's Wikibase URL: ").strip()



		wbi=WikibaseIntegrator()

	#TODO: move to config yaml
	if(login):
		wikibase_user = input("Introduce wikibase username: ").strip()
		wikibase_pwd = input("Introduce wikibase password: ").strip()


		#change the USER_AGENT config parameter to edit the User-Agent header. See https://www.wikidata.org/wiki/Wikidata:Data_access for more info
		wbi_config['USER_AGENT'] = 'SALTbot/1.0 (https://www.wikidata.org/wiki/User:'+wikibase_user+')'

	
		wbi_login_instance = wbi_login.Clientlogin(user=wikibase_user, password=wikibase_pwd)
		wbi = WikibaseIntegrator(login=wbi_login_instance)

	if(jsonfile):

		print()
		operation = "JSONFILE: " + jsonfile
		click.echo(click.style(operation, fg='yellow', bold=True))
		try:
			f = open(jsonfile, 'r')
		except:
			sys.exit("SALTbot ERROR: Path provided as JSON file parameter is invalid")


		info = json.loads(f.read())
		operation_list = SALTbot2.SALTbot(info, wbi, wb_article_Qnode, wb_software_Qnode, wb_instanceOf_Pnode, wb_subclassOf_Pnode, wb_mainSubject_Pnode, wb_describedBySource_Pnode)
		

		
	elif(url):

		print()
		operation = "URL: " + url
		click.echo(click.style(operation, fg='yellow', bold=True))

		if(output):

			os.system("somef describe -r "+url+" -o "+output+" -t 0.8")
			try:
				f = open(output,"r")
			except:
				sys.exit("SALTbot ERROR: url is not a valid repository")

		else:
			now = datetime.now().time()
			fich = str(now).replace(":", "") + ".json"
			os.system("somef describe -r "+url+" -o "+fich+" -t 0.8")

			try:
				f = open(fich,"r")
			except:
				sys.exit("SALTbot ERROR: url is not a valid repository")

		info = json.loads(f.read())
		operation_list = SALTbot2.SALTbot(info, wbi, wb_article_Qnode, wb_software_Qnode, wb_instanceOf_Pnode, wb_subclassOf_Pnode, wb_mainSubject_Pnode, wb_describedBySource_Pnode)
		
		
					
	if(operation_list!=[]):
			print()
			click.echo(click.style('SALTbot WILL INTRODUCE THESE STATEMENTS IN WIKIDATA', fg='red', bold = True))
			for operation in operation_list:
				print(operation)
				#for j in i:
				#	if j[1]=='P921':
				#		print("| ARTICLE:  ", j[0][0]," : ", j[0][1], " | PROPERTY: ", j[1], " : main_subject | SOFTWARE: ", j[2][0], " : ", j[2][1], " |")
				#	elif j[1]=='P1343':
				#		print("| SOFTWARE:  ", j[0][0]," : ", j[0][1], " | PROPERTY: ", j[1], " : described_by_source | ARTICLE: ", j[2][0], " : ", j[2][1], " |")

					
#HACER EL TRATAMIENTO DE STATEMENTS COMO FUNCION
			print()
			confirmation = input("CONFIRM (Y/N): ").strip()

			while(confirmation != "Y" and confirmation != "N"):
				confirmation = input("ONLY Y OR N ARE VALID CONFIRMATION ANSWERS. CONFIRM (Y/N): ").strip()	

			if(confirmation == "Y" and upload == True):
				SALTbot2.uploadChanges(info, operation_list, wbi)
				
	



if(__name__=='__main__'):
	main()
