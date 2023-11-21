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

import SALTbotHandler
import SALTbotUpdater



#@click.group(context_settings={'help_option_names': ['-h', '--help']})
@click.group()
def cli():
    click.echo("SALTbot: Software and Article Linker Toolbot")




@click.command()
@click.option('-a', '--auto', help="Automatically configures SALTbot to target Wikidata", is_flag=True, default=True)
def configure(auto):
	"""Configure SALTbot"""
	config = {}
	config['USER'] = click.prompt("Wikibase user", default = "")
	config['PASSWORD'] = click.prompt("Wikibase Password", default = "")

	if(auto):
		click.echo('Introduce the target wikibase data. If left blank, it will default to target Wikidata')
		config['MEDIAWIKI_API_URL'] = click.prompt("MEDIAWIKI_API_URL", default = "")
		config['SPARQL_ENDPOINT_URL'] = click.prompt("SPARQL_ENDPOINT_URL", default = "")
		config['WIKIBASE_URL'] = click.prompt("WIKIBASE_URL", default = "")
	else:
		config['MEDIAWIKI_API_URL'] = None
		config['SPARQL_ENDPOINT_URL'] = None
		config['WIKIBASE_URL'] = None
	
	stream = open('config.yaml', 'w')
	yaml.dump(config, stream)

	click.secho(f"Success", fg="green")


#@click.command(help='Run SALTbot')
@click.command()
@click.option('--auto', '-a', is_flag=True, help='Sets bot to auto mode. The bot will not ask for user confirmations and will only require supervision if one or more articles or software are found in Wikidata.')
@click.option('--output', '-o', default=None, type = click.Path(), help='If url is used, this will be the path of the metadata output produced by SOMEF.')
@optgroup.group('Input', cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option('--url', '-u', help = 'URL of the remote target repository.')
@optgroup.option('--urlfile','-ru', type = click.Path(exists=True), help='File with one or more url entries to be treated. SALTbot will analyze each individual url in succesion and introduce the links afterwards.')
@optgroup.option('--jsonfile','-js', type = click.Path(exists=True), help='Path to the JSON extracted from the target repository with SOMEF.')
@optgroup.option('--jsondir', '-rjs', type = click.Path(exists=True), help = 'Path of a directory with one or multiple JSONs extracted with SOMEF. SALTbot will analyze each individual json in succesion and introduce the links afterwards.')
def run(jsonfile, url, urlfile, jsondir, auto,  output):
	"""Run SALTbot"""
	
	try:
		stream = open('config.yaml', 'r')   
		config_data = yaml.load(stream, Loader = SafeLoader)
	except Exception as e:
		print(e)
		click.echo('SALTbot Error: Configuration file not found')
		return

	user = config_data['USER']
	passw = config_data['PASSWORD']

	if config_data['MEDIAWIKI_API_URL']!='':
		#print(config_data['MEDIAWIKI_API_URL'])
		wbi_config['MEDIAWIKI_API_URL'] = config_data['MEDIAWIKI_API_URL']
	if config_data['SPARQL_ENDPOINT_URL']!='':
		#print(config_data['SPARQL_ENDPOINT_URL'])
		wbi_config['SPARQL_ENDPOINT_URL'] = config_data['SPARQL_ENDPOINT_URL']
	if config_data['WIKIBASE_URL']!='':
		#print(config_data['WIKIBASE_URL'])
		wbi_config['WIKIBASE_URL'] = config_data['WIKIBASE_URL']


	wbi_config['USER_AGENT'] = 'SALTbot/1.0 (https://www.wikidata.org/wiki/User:'+user+')'
	
	wbi=WikibaseIntegrator(login=wbi_login.Clientlogin(user=user, password=passw))

	#MANDATORY NODES (instance_of, main_subject, described_by_source, scientific article, software category, free software)
	man_nodes = {}
	#print(config_data)
	#return
	try:
		man_nodes = SALTbotHandler.getMandatoryNodes(wbi, config_data)
	except Exception as e:
		return
	

		

	#software props
	opt_nodes = {}
	opt_nodes = SALTbotHandler.getOptionalNodes(wbi, config_data)
	
	
	
	
	#Change this to true if you wish to edit wikidata
	upload = True

	operation_list = []

	results = {}

	result_dump = open('results.txt', 'a')

	if(jsonfile):

		print()
		operation = "JSONFILE: " + jsonfile
		click.echo(click.style(operation, fg='yellow', bold=True))
		try:
			f = open(jsonfile, 'r')
		except:
			sys.exit("SALTbot ERROR: Path provided as JSON file parameter is invalid")


		info = json.loads(f.read())
		operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results)
		#print('results final', results)
		if len(operation_list) > 0:
			SALTbotUpdater.executeOperations(operation_list,auto,wbi)
			for i in results:
				result_dump.write(str(i)+':'+str(results[i])+'\n')
		
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
		operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results)
		if len(operation_list) > 0:
			SALTbotUpdater.executeOperations(operation_list,auto, wbi)
		#print('results final', results)
			for i in results:
				result_dump.write(str(i)+':'+str(results[i])+'\n')
		
	elif(urlfile):
		try:
			f = open(urlfile,"r")
		except:
			sys.exit("SALTbot ERROR: urlfile is not a valid file")
		
		urls = f.readlines()

		urls = [u.rstrip() for u in urls]


		
		
		for i in urls:
			print()
			operation = "URL: " + i
			click.echo(click.style(operation, fg='yellow', bold=True))

		
			o=urlparse(i)

			
			if(output):
				filename = output + o.path.replace("/", " ").split()[1] + ".json"
			else:
				filename = o.path.replace("/", " ").split()[1] + ".json"
		
			os.system("somef describe -r "+i+" -o "+filename+" -t 0.8")

			try:
				f = open(filename,"r")
			except:
				print("SALTbot ERROR: no files")
			
			info = json.loads(f.read())
			operation_list = operation_list + SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results)
			#print(operation_list)
			if len(operation_list) > 10:
				SALTbotUpdater.executeOperations(operation_list,auto, wbi)
				operation_list = []
				for i in results:
					result_dump.write(str(i)+':'+str(results[i])+'\n')
				results = {}
		
		if operation_list != []:
			SALTbotUpdater.executeOperations(operation_list,auto, wbi)
			for i in results:
				result_dump.write(str(i)+':'+str(results[i])+'\n')
			

	elif(jsondir):
		

		alljsons = jsondir+'/*.json'

	
		for jsonfile in glob.glob(alljsons):
			
			print()
			operation = "JSONFILE: " + jsonfile
			click.echo(click.style(operation, fg='yellow', bold=True))

			f = open(jsonfile, 'r')
			info = json.loads(f.read())
			operation_list = operation_list + SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results)

			if len(operation_list) > 10:
				SALTbotUpdater.executeOperations(operation_list,auto, wbi)
				operation_list = []
				for i in results:
					result_dump.write(str(i)+':'+str(results[i])+'\n')
				results = {}

		if operation_list != []:
			SALTbotUpdater.executeOperations(operation_list,auto,wbi)
			for i in results:
				result_dump.write(str(i)+':'+str(results[i])+'\n')
		
	result_dump.close()	

cli.add_command(configure)
cli.add_command(run)




if(__name__=='__main__'):
	cli()
