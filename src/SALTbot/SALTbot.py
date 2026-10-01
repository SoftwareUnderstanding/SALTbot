#!/home/jorge/TFG/TFGenv/bin/python
import json
import os
import subprocess
import sys
from urllib.parse import urlparse

import yaml
from yaml.loader import SafeLoader

import re
from pathlib import Path
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from datetime import datetime

import glob
from wikibaseintegrator import WikibaseIntegrator
from wikibaseintegrator.wbi_config import config as wbi_config
from wikibaseintegrator import wbi_login
from wikibaseintegrator import wbi_helpers

from . import SALTbotHandler
from . import SALTbotUpdater


OPERATIONS_DIR = Path("operations")
RESULTS_DIR = Path("results")
FINAL_OPERATION_LIST = Path("final_operation_list.txt")

def cleanFinalOperationList():
	if FINAL_OPERATION_LIST.exists():
		FINAL_OPERATION_LIST.unlink()


def sanitizeFilePart(value):
	cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
	cleaned = cleaned.strip("._")
	return cleaned or "unknown"


def getOperationsFilePath(repo_url):
	parsed_url = urlparse(repo_url)
	path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

	if len(path_parts) >= 2:
		organization = sanitizeFilePart(path_parts[0])
		repository = sanitizeFilePart(path_parts[1])
	else:
		organization = sanitizeFilePart(parsed_url.netloc or "unknown")
		repository = sanitizeFilePart(path_parts[0] if path_parts else "repository")

	return OPERATIONS_DIR / f"{organization}_{repository}_operations.txt"


def getResultsFilePath(repo_url):
	parsed_url = urlparse(repo_url)
	path_parts = [part for part in parsed_url.path.strip("/").split("/") if part]

	if len(path_parts) >= 2:
		organization = sanitizeFilePart(path_parts[0])
		repository = sanitizeFilePart(path_parts[1])
	else:
		organization = sanitizeFilePart(parsed_url.netloc or "unknown")
		repository = sanitizeFilePart(path_parts[0] if path_parts else "repository")

	return RESULTS_DIR / f"{organization}_{repository}_results.txt"


def writeOperationsFile(repo_url, operation_list):
	OPERATIONS_DIR.mkdir(exist_ok=True)

	operation_file = getOperationsFilePath(repo_url)

	with operation_file.open("w", encoding="utf-8") as operation_dump:
		for operation in operation_list:
			operation_dump.write(str(operation) + "\n")

	return operation_file


def writeResultsFile(repo_url, repo_result):
	RESULTS_DIR.mkdir(exist_ok=True)

	result_file = getResultsFilePath(repo_url)
	temp_file = result_file.with_name(result_file.name + f".{os.getpid()}.tmp")

	try:
		with temp_file.open("w", encoding="utf-8") as result_dump:
			result_dump.write(str(repo_url) + ":" + str(repo_result) + "\n")

		temp_file.replace(result_file)
	finally:
		if temp_file.exists():
			temp_file.unlink()

	return result_file


def getOperationFiles(operations_dir):
	return sorted(Path(operations_dir).glob("*_operations.txt"))


def buildFinalOperationList(operations_dir):
	operation_files = getOperationFiles(operations_dir)

	with FINAL_OPERATION_LIST.open("w", encoding="utf-8") as final_dump:
		for operation_file in operation_files:
			with operation_file.open("r", encoding="utf-8") as operation_dump:
				for operation in operation_dump:
					final_dump.write(operation)
					if not operation.endswith("\n"):
						final_dump.write("\n")

	return FINAL_OPERATION_LIST, operation_files


def clearOperationFiles(operation_files):
	for operation_file in operation_files:
		operation_file.unlink()


def operationFileHasContent(operation_file):
	return Path(operation_file).read_text(encoding="utf-8").strip() != ""

def runSomefDescribe(repo_url, output, github_api_token):
	command = ["somef", "describe", "-r", repo_url, "-o", output, "-t", "0.8"]

	if github_api_token:
		command.extend(["--github-token", github_api_token])

	try:
		subprocess.run(command, check=True)
	except FileNotFoundError:
		sys.exit("SALTbot ERROR: SOMEF command was not found")
	except subprocess.CalledProcessError as e:
		sys.exit("SALTbot ERROR: SOMEF failed with exit code " + str(e))



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
	config['GITHUB_API_TOKEN'] = click.prompt("GitHub API Token", default = "", hide_input=True)
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

@click.command()
@click.option('--file','-f', type = click.Path(exists=True, dir_okay=False), help='Statement operations outputted by SALTbot using describe command')
@click.option('--operations-dir', type = click.Path(exists=True, file_okay=False), help='Directory with operation files to merge into final_operation_list.txt before updating Wikibase.')
@click.option('--auto', '-a', is_flag=True, help='Sets bot to auto mode. The bot will not ask for user confirmations and will only require supervision if one or more articles or software are found in Wikidata.')
def update(file, operations_dir, auto):
	"""Update Statements provided by file into target Wikibase"""

	if (file is None and operations_dir is None) or (file is not None and operations_dir is not None):
		click.echo('SALTbot Error: provide exactly one of --file or --operations-dir')
		return

	if operations_dir:
		file, operation_files = buildFinalOperationList(operations_dir)
		click.echo('Merged ' + str(len(operation_files)) + ' operation files into ' + str(file))

		if operation_files == []:
			click.echo('SALTbot did not find operation files to update')
			return

	if not operationFileHasContent(file):
		click.echo('SALTbot did not find operations to update')

		if operations_dir:
			clearOperationFiles(operation_files)

		return

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
	
	wbi=WikibaseIntegrator(login=wbi_login.Login(user=user, password=passw))

	with open(file, 'r', encoding='utf-8') as operation_list:
		#operation_list = json.loads(operations)
		SALTbotUpdater.executeOperations(operation_list,auto,wbi)

	if operations_dir:
		clearOperationFiles(operation_files)


#@click.command(help='Run SALTbot')
@click.command()
@click.option('--auto', '-a', is_flag=True, help='Sets bot to auto mode. The bot will not ask for user confirmations and will only require supervision if one or more articles or software are found in Wikidata.')
@click.option('--output', '-o', default=None, type = click.Path(), help='If url is used, this will be the path of the metadata output produced by SOMEF.')
@click.option('--fallback-search',is_flag=True,default=False,help='Search Wikidata by repository name when SOMEF does not detect a scientific article.')
@optgroup.group('Input', cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option('--url', '-u', help = 'URL of the remote target repository.')
@optgroup.option('--urlfile','-ru', type = click.Path(exists=True), help='File with one or more url entries to be treated. SALTbot will analyze each individual url in succesion and introduce the links afterwards.')
@optgroup.option('--jsonfile','-js', type = click.Path(exists=True), help='Path to the JSON extracted from the target repository with SOMEF.')
@optgroup.option('--jsondir', '-rjs', type = click.Path(exists=True), help = 'Path of a directory with one or multiple JSONs extracted with SOMEF. SALTbot will analyze each individual json in succesion and introduce the links afterwards.')
def describe(jsonfile, url, urlfile, jsondir, auto,  output,fallback_search):
	"""Creates the statements to link software and articles"""
	
	try:
		stream = open('config.yaml', 'r')   
		config_data = yaml.load(stream, Loader = SafeLoader)
		#print(config_data)
	except Exception as e:
		print(e)
		click.echo('SALTbot Error: Configuration file not found')
		return

	user = config_data['USER']
	passw = config_data['PASSWORD']
	github_api_token = config_data.get('GITHUB_API_TOKEN', '')
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
	
	wbi=WikibaseIntegrator(login=wbi_login.Login(user=user, password=passw))

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

	cleanFinalOperationList()
	OPERATIONS_DIR.mkdir(exist_ok=True)
	RESULTS_DIR.mkdir(exist_ok=True)

	if(jsonfile):

		print()
		operation = "JSONFILE: " + jsonfile
		click.echo(click.style(operation, fg='yellow', bold=True))
		try:
			f = open(jsonfile, 'r')
		except:
			sys.exit("SALTbot ERROR: Path provided as JSON file parameter is invalid")


		info = json.loads(f.read())
		operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results, fallback_search, config_data)

		#print('results final', results)
		repo_url = info["code_repository"][0]["result"]["value"]
		result_file = writeResultsFile(repo_url, results[repo_url])
		print("Results written to", result_file)
		operation_file = writeOperationsFile(repo_url, operation_list)
		print("Operations written to", operation_file)
		
			
		
	elif(url):

		print()
		operation = "URL: " + url
		click.echo(click.style(operation, fg='yellow', bold=True))

		if(output):

			runSomefDescribe(url, output, github_api_token)
			try:
				f = open(output,"r")
			except:
				sys.exit("SALTbot ERROR: url is not a valid repository")

		else:
			now = datetime.now().time()
			fich = str(now).replace(":", "") + ".json"
			runSomefDescribe(url, fich, github_api_token)

			try:
				f = open(fich,"r")
			except:
				sys.exit("SALTbot ERROR: url is not a valid repository")

		info = json.loads(f.read())
		operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results, fallback_search, config_data)

		#print('results final', results)
		repo_url = info["code_repository"][0]["result"]["value"]
		result_file = writeResultsFile(repo_url, results[repo_url])
		print("Results written to", result_file)
		operation_file = writeOperationsFile(repo_url, operation_list)
		print("Operations written to", operation_file)

		
		#if len(operation_list) > 0:
		#	SALTbotUpdater.executeOperations(operation_list,auto, wbi)
		#print('results final', results)
			
		
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
		
			runSomefDescribe(i, filename, github_api_token)

			try:
				f = open(filename,"r")
			except:
				print("SALTbot ERROR: no files")
			
			info = json.loads(f.read())
			repo_operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results, fallback_search, config_data)
			repo_url = info["code_repository"][0]["result"]["value"]
			result_file = writeResultsFile(repo_url, results[repo_url])
			print("Results written to", result_file)
			operation_file = writeOperationsFile(repo_url, repo_operation_list)
			print("Operations written to", operation_file)
			operation_list = operation_list + repo_operation_list
			#print(operation_list)
			#if len(operation_list) > 10:
			#	SALTbotUpdater.executeOperations(operation_list,auto, wbi)
			#	operation_list = []
		#print('results final', results)
		#if operation_list != []:
		#	SALTbotUpdater.executeOperations(operation_list,auto, wbi)
	elif(jsondir):
		

		alljsons = jsondir+'/*.json'

	
		for jsonfile in glob.glob(alljsons):
			
			print()
			operation = "JSONFILE: " + jsonfile
			click.echo(click.style(operation, fg='yellow', bold=True))

			f = open(jsonfile, 'r')
			info = json.loads(f.read())
			repo_operation_list = SALTbotHandler.SALTbot(wbi, info, man_nodes, opt_nodes, auto, results, fallback_search, config_data)
			repo_url = info["code_repository"][0]["result"]["value"]
			result_file = writeResultsFile(repo_url, results[repo_url])
			print("Results written to", result_file)
			operation_file = writeOperationsFile(repo_url, repo_operation_list)
			print("Operations written to", operation_file)
			operation_list = operation_list + repo_operation_list

		#if operation_list != []:
		#	SALTbotUpdater.executeOperations(operation_list,auto,wbi)
		#print('results final', results)
		
cli.add_command(configure)
cli.add_command(update)
cli.add_command(describe)




if(__name__=='__main__'):
	cli()
