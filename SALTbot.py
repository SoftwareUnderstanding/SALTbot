#!/home/jorge/TFG/TFGenv/bin/python
import json
import os
import sys
from urllib.parse import urlparse
from numpy import True_
import yaml
from yaml.loader import SafeLoader
import bibtexparser
import requests
import time
import click
from click_option_group import optgroup, RequiredMutuallyExclusiveOptionGroup
from datetime import datetime
import pywikibot
import glob

#devuelve un diccionario con el Qnode como Key y su label como value
def getEntitiesByName(url, name, entityType):

	result_set = {}

	if(entityType == 0):

		query = '''SELECT DISTINCT ?item ?itemlabel WHERE {

					  SERVICE wikibase:mwapi {
					    bd:serviceParam wikibase:endpoint "www.wikidata.org";
					                    wikibase:api "EntitySearch";
					                    mwapi:search \"'''+name+'''\";
					                    mwapi:language "en".
					    ?item wikibase:apiOutputItem mwapi:item.
						?num wikibase:apiOrdinal true.
					  				} 										#Extraer Entidades con noombre parecido a name

					  ?item wdt:P31 wd:Q13442814. #Elegir Entidades que sean instancia de articulo cientifico

		  	  		  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
		  						   				?item rdfs:label ?itemlabel
					  					} #Extraer nombre de entidad
					  }

		'''
		#print(query)
	elif(entityType == 1):

		query = '''SELECT DISTINCT ?item ?itemlabel WHERE {

						  SERVICE wikibase:mwapi {
						    bd:serviceParam wikibase:endpoint "www.wikidata.org";
						                    wikibase:api "EntitySearch";
						                    mwapi:search \"'''+name+'''\";
						                    mwapi:language "en".
						    ?item wikibase:apiOutputItem mwapi:item.
							?num wikibase:apiOrdinal true.
						  } 										#Extraer Entidades con noombre parecido a name

						   ?item wdt:P31 ?instancia. #software es instancia de la metaclase software
				   	       ?instancia wdt:P31 wd:Q17155032.

			  	  		  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
			  						   				?item rdfs:label ?itemlabel
						  } #Extraer nombre de entidad
						  }
			'''

	r = requests.get(url, params = {'format': 'json', 'query': query})
	data = r.json()

	results = data['results']['bindings']



	for i in results:
		o=urlparse(i['item']['value'])
		aux1 = o.path.replace("/", " ")
		result_set.update({aux1.split()[1] : i['itemlabel']['value']})

	return result_set


def softwaresEnlazados(url, Qnode_Articulo):
	query = '''SELECT DISTINCT ?software ?softwarelabel WHERE {

								  wd:'''+Qnode_Articulo+''' wdt:P921 ?software. 	#articulo tiene como main subject a software

								  ?software wdt:P31 ?instancia. 					#software es instancia de la metaclase software
							      ?instancia wdt:P31 wd:Q17155032.

								  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en".
	  														?software rdfs:label ?softwarelabel}
							}'''
	#print(query)
	r = requests.get(url, params = {'format': 'json', 'query': query})
	data = r.json()

	#print(data)
	results = data['results']['bindings']

	result_set = {}

	for i in results:
		o=urlparse(i['software']['value'])
		aux1 = o.path.replace("/", " ")
		result_set.update({aux1.split()[1] : i['softwarelabel']['value']})

	return result_set

def articulosEnlazados(url, Qnode_Software):

	query = '''SELECT DISTINCT ?articles ?articlelabel WHERE {
	  				wd:'''+Qnode_Software+''' wdt:P1343 ?articles. #software es descrito por articulo

      				?articles wdt:P31 wd:Q13442814. #articulo es de la clase schorlarly article

	  				SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en" .
	  										 ?articles rdfs:label ?articlelabel}
				}'''

	r = requests.get(url, params = {'format': 'json', 'query': query})
	data = r.json()

	results = data['results']['bindings']


	result_set = {}

	for i in results:
		o=urlparse(i['articles']['value'])
		aux1 = o.path.replace("/", " ")
		result_set.update({aux1.split()[1] : i['articlelabel']['value']})

	return result_set


def checkEnlaces(enlaces_Articulo, enlaces_Software, Qnode_a, Qnode_s):

	enlace_articulo_software=0
	enlace_software_articulo=0



	try:
		if Qnode_a in enlaces_Software[Qnode_s]:
			
			enlace_software_articulo = 1

	except:
		pass
	try:
		if Qnode_s in enlaces_Articulo[Qnode_a]:
			enlace_articulo_software = 1
	except:
		pass
	
	
	return (enlace_articulo_software, enlace_software_articulo)



def print_links(selected_article_qnode, selected_software_qnode, res):
	print()
	if(res==(1, 1)):

		click.echo(click.style('ARTICLE ALREADY LINKED WITH SOFTWARE', fg='green', bold =True))
		click.echo(click.style('SOFTWARE ALREADY LINKED WITH ARTICLE', fg='green', bold =True))
		return 

	elif(res==(1, 0)):

		click.echo(click.style('ARTICLE ALREADY LINKED WITH SOFTWARE', fg='green', bold =True))
		click.echo(click.style('SALTbot WILL INTRODUCE THE SOFTWARE-ARTICLE LINK IN WIKIDATA', bold =True))
		return [(selected_software_qnode, "P1343",  selected_article_qnode)]


	elif(res==(0, 1)):

		click.echo(click.style('SOFTWARE ALREADY LINKED WITH ARTICLE', fg='green', bold =True))
		click.echo(click.style('SALTbot WILL INTRODUCE THE ARTICLE-SOFTWARE LINK IN WIKIDATA', bold =True))
	
		return [(selected_article_qnode, "P921", selected_software_qnode)]

	elif(res==(0, 0)):

		click.echo(click.style('SALTbot WILL INTRODUCE THE ARTICLE-SOFTWARE LINK IN WIKIDATA', bold =True))
		click.echo(click.style('SALTbot WILL INTRODUCE THE SOFTWARE-ARTICLE LINK IN WIKIDATA', bold =True))
		
		return [(selected_software_qnode, "P1343",  selected_article_qnode), (selected_article_qnode, "P921", selected_software_qnode)]


def SALTbot(info, keyword, auto):

	parsedinfo = []

	#Si tiene cita
	if("citation" in info.keys()):


		#por cada tecnica de extracción
		for i in info["citation"]:

			#si la tecnica es File Exploration o Regular expression
			if(i["technique"] == "File Exploration" or i["technique"] == "Regular expression"):
				#se intenta parsear el BIB
				try:
					parsedinfo.append(("BIB", bibtexparser.loads(i["excerpt"]), i["technique"]))

				#Si falla el parsing es porque está en YAML
				except:
					parsedinfo.append(("YAML", yaml.load(i["excerpt"], Loader = SafeLoader), "FILE EXP"))



	print("\n")

	click.echo(click.style('TITLE EXTRACTION', fg='red', bold=True))

	print("\n")

	# si se ha encontrado al menos un titulo
	if(parsedinfo != []):

		#Por cada titulo
		for i in parsedinfo:

			#si es BIB
			if(i[0]=="BIB"):

				#Se imprime el titulo
				try:
					print("DETECTED TITLE: ", i[1].entries[0]["title"], "     ", "TECHNIQUE: ", i[2])

				#si el archivo se ha parseado mal se elimina
				except:
					parsedinfo.remove(i)

			#si es YAML
			elif(i[0]=="YAML"):

				#Se imprime el titulo
				try:
					print("DETECTED TITLE: ", i[1]["title"], "     ", "TECHNIQUE: ", i[2])

				#si el archivo se ha parseado mal se elimina
				except:
					parsedinfo.remove(i)


	#Si no se encuentran titulos
	if(parsedinfo == []):
		print("NO DETECTED TITLES")



	url = 'https://query.wikidata.org/sparql'
	set_articulos = {}
	set_softwares = {}


	#por cada elemento en la lista de titulos
	for i in parsedinfo:

		#si es BIB se extrae del bibtex
		if(i[0] == "BIB"):
			concat_query = i[1].entries[0]["title"]

		#si es YAML se extrae del YAML
		elif(i[0] == "YAML"):
			concat_query = i[1]["title"]


		#Se normaliza el titulo
		concat_query = concat_query.replace("{", "")
		concat_query = concat_query.replace("}", "")


		#Se buscan las entidades de los articulos
		result_articulos = getEntitiesByName(url, concat_query, 0)
		time.sleep(1)

		#Si encuentra entidades se añaden al conjunto de articulos
		if(result_articulos != {}):
			set_articulos = set_articulos | result_articulos




	#Si no ha encontrado nada
	if(set_articulos == {}):
		print("NO ARTICLES DETECTED - TRYING NAME SEARCH")

		if(keyword == None):
			#Se buscan todos los articulos a partir del nombre del repositorio
			set_articulos = getEntitiesByName(url, info['name']['excerpt'], 0)

		else:
			set_articulos = getEntitiesByName(url, keyword, 0)

		time.sleep(1)




	enlaces_articulo_software = {}
	enlaces_software_articulo = {}

	#Por cada articulo
	for i in set_articulos:

		#Se buscan sus softwares enlazados
		result_software = softwaresEnlazados(url, i)
		time.sleep(1)



		if(result_software!={}):
			#se añaden al set de softwares
			set_softwares = set_softwares | result_software

			#se añaden los softwares al diccionario de articulos-software
			enlaces_articulo_software.update({i:result_software})




	if(enlaces_articulo_software == {}):
		print("NO SOFTWARES DETECTED - TRYING NAME SEARCH")

		if(keyword == None):
			#se buscan todos los softwares a partir del nombre del repositorio
			set_softwares = getEntitiesByName(url, info['name']['excerpt'], 1)
		else:
			set_softwares = getEntitiesByName(url, keyword, 1)

		time.sleep(1)


	#comprobar enlaces_completos

	#por cada software
	for i in set_softwares:
		#se buscan los articulos enlazados
		result_articulo = articulosEnlazados(url, i)
		time.sleep(1)

		if(result_articulo != {}):
			enlaces_software_articulo.update({i:result_articulo})



	print("\n")
	click.echo(click.style('RESULTS FOUND ON WIKIDATA: ', fg='red', bold=True))
	print("\n")
	click.echo(click.style('ARTICLES: ', bold=True))
	for i in set_articulos:
		print(i, " : ", set_articulos[i])

	print("\n")
	click.echo(click.style('SOFTWARES: ', bold=True))
	for i in set_softwares:
		print(i, " : ", set_softwares[i])

	print("\n")
	click.echo(click.style('CLASIFICATION', fg='red', bold = True))
	print("\n")


	click.echo(click.style('ARTICLES LINKED WITH SOFTWARE: ', bold=True))

	non_recognised_articles = {}
	non_recognised_softwares = {}

	for i in enlaces_articulo_software:
		for j in enlaces_articulo_software[i]:
			try:
				print("| ",i, " : ", set_articulos[i], " | IS LINKED WITH SOFTWARE | ", j, " : ", set_softwares[j], " |")
			except:
				non_recognised_softwares.update({j:i})


	print()
	click.echo(click.style('SOFTWARE LINKED WITH ARTICLES: ', bold=True))

	
	for i in enlaces_software_articulo:
		for j in enlaces_software_articulo[i]:
			try:
				print("| ",i, " : ", set_softwares[i], " | IS LINKED WITH ARTICLE | ", j, " : ", set_articulos[j], " |")
			except:
				non_recognised_articles.update({j:i})


	print("\n")



	if(set_articulos != {} ):


		click.echo(click.style('LINKING', fg='red', bold =True))
		print()
		contador = 0
		map_articulos = {}
		click.echo(click.style('SELECT AN ARTICLE : ', fg='blue', bold = True))

		for i in set_articulos:
			contador = contador + 1
			print(contador, " - ", i, " : ", set_articulos[i])
			map_articulos.update({str(contador):i})



		print()
		inp_articulo = input("ARTICLE NUMBER: ").strip()

		while(inp_articulo not in map_articulos):
			inp_articulo = input("NOT A VALID ARTICLE. CHOOSE ANOTHER ARTICLE NUMBER: ").strip()


		print()
		contador = 0
		map_softwares = {}
		if(set_softwares!={}):
			click.echo(click.style('SELECT A SOFTWARE : ', fg='blue', bold = True))

			for i in set_softwares:
				contador = contador + 1
				print(contador, " - ", i, " : ", set_softwares[i])
				map_softwares.update({str(contador):i})


			inp_software = input("SOFTWARE NUMBER: ").strip()

			while(inp_software not in map_softwares):
				inp_software = input("NOT A VALID SOFTWARE. CHOOSE ANOTHER SOFTWARE NUMBER: ").strip()


			res = checkEnlaces(enlaces_articulo_software, enlaces_software_articulo, map_articulos[inp_articulo], map_softwares[inp_software])
			
		else:
			res = (0,0)
			inp_software = None



		dict_translated_entities = {"pytorch":("Q224971","Q224970"), "kgtk":("Q224971","Q224970"), "intermine":("Q224971","Q224970"), "bitcoin":("Q224971","Q224970"), "Widoco":("Q224971",None)}

		main_subject_test_wikidata = u'P96293'
		described_by_source_test_wikidata = u'P96292'
		has_source_repository_test_wikidata = u''


		name = info['name']['excerpt']

		

		selected_article_qnode = map_articulos[inp_articulo]

		if(inp_software!= None):
			selected_software_qnode = map_softwares[inp_software]
			return ((selected_article_qnode, set_articulos[selected_article_qnode]), (selected_software_qnode, set_softwares[selected_software_qnode]), res)

		else:
			selected_software_qnode = None
			return ((selected_article_qnode, set_articulos[selected_article_qnode]), (None, None), res)

		




@click.group(context_settings={'help_option_names': ['-h', '--help']})
def cli():
    print("SALTbot: Software and Article Linker Toolbot")


@click.command()
@click.option('--auto', '-a', is_flag=True, help='Sets bot to auto mode. The bot will not ask for user confirmations and will only require supervision if one or more articles or software are found in Wikidata.')
@click.option('--keyword', '-k', default = None, help = 'Keyword for searching in case the repository treatment found no articles or software on Wikidata.')
@click.option('--output', '-o', default=None, type = click.Path(), help='If url is used, this will be the path of the metadata output produced by SOMEF.')

@optgroup.group('Input', cls=RequiredMutuallyExclusiveOptionGroup)
@optgroup.option('--readmedir', '-rdir', type = click.Path(exists=True), help = 'Path to the target repository if the repository is local.')
@optgroup.option('--url', '-u', help = 'URL of the remote target repository.')
@optgroup.option('--urlfile','-ru', type = click.Path(exists=True), help='File with one or more url entries to be treated. SALTbot will analyze each individual url in succesion and introduce the links afterwards.')
@optgroup.option('--jsonfile','-js', type = click.Path(exists=True), help='Path to the JSON extracted from the target repository with SOMEF.')
@optgroup.option('--jsondir', '-rjs', type = click.Path(exists=True), help = 'Path of a directory with one or multiple JSONs extracted with SOMEF. SALTbot will analyze each individual json in succesion and introduce the links afterwards.')




def main(readmedir, jsonfile, url, urlfile, jsondir, auto, keyword,  output):

	#Edit this values to the target nodes in wikidata
	qnode_article_test = 'Q225102'
	qnode_software_test = 'Q225101'
	main_subject_test ='P96347'
	described_by_source_test = 'P96348'
	
	#Change this to true if you wish to edit wikidata
	upload = True

	operation_list = []

	if(readmedir):
		print()
		operation = "README: " + readmedir
		click.echo(click.style(operation, fg='yellow', bold=True))

		if(output):

			os.system("somef describe -d "+readmedir+" -o "+output+" -t 0.8")
			try:
				f = open(output,"r")
			except:
				sys.exit("SALTbot ERROR: Path provided as README file parameter is invalid")

			

		else:
			now = datetime.now().time()
			fich = str(now).replace(":", "") + ".json"
			os.system("somef describe -r "+url+" -o "+fich+" -t 0.8")

			try:
				f = open(fich,"r")
			except:
				sys.exit("SALTbot ERROR: Path provided as README file parameter is invalid")


		info = json.loads(f.read())
		ret = SALTbot(info, keyword, auto)
		
		
		if(ret == None):
			print("No articles detected, SALTbot will not introduce anything to wikidata")
		else: 
			if(ret[1]!=None):
				aux = print_links(ret[0], ret[1], ret[2])
				if aux != None:
					operation_list.append(aux)

			else:
				site = pywikibot.Site("test", "wikidata")

				message_summary = u'Creating new software: ' + info['name']['excerpt']
				test_name = "SALTbot test : "+info['name']['excerpt']
				label_dict = {"en": test_name}

				
				if(upload==True):
					new_software = pywikibot.ItemPage(site)

					new_software.editLabels(labels=label_dict, summary=message_summary)

					software_qnode = new_software.getID()
				
					operation_list.append(print_links(ret[0], (software_qnode, test_name), ret[2]))
				else:
					operation_list.append(print_links(ret[0], (None, test_name), ret[2]))
			
			

		

	elif(jsonfile):

		print()
		operation = "JSONFILE: " + jsonfile
		click.echo(click.style(operation, fg='yellow', bold=True))
		try:
			f = open(jsonfile, 'r')
		except:
			sys.exit("SALTbot ERROR: Path provided as JSON file parameter is invalid")


		info = json.loads(f.read())
		ret = SALTbot(info, keyword, auto)
		
		
		
		if(ret == None):
			print("No articles detected, SALTbot will not introduce anything to wikidata")
		else: 
			if(ret[1]!=(None, None)):
				aux = print_links(ret[0], ret[1], ret[2])
				
				if aux != None:
					operation_list.append(aux)
				
			else:
				
				site = pywikibot.Site("test", "wikidata")

				message_summary = u'Creating new software: ' + info['name']['excerpt']
				test_name = "SALTbot test : "+info['name']['excerpt']
				label_dict = {"en": test_name}

				
				if(upload == True):
					new_software = pywikibot.ItemPage(site)

					new_software.editLabels(labels=label_dict, summary=message_summary)

					software_qnode = new_software.getID()
				
					operation_list.append(print_links(ret[0], (software_qnode, test_name), ret[2]))
				else:
					operation_list.append(print_links(ret[0], (None, test_name), ret[2]))
			
			


		

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
		ret = SALTbot(info, keyword, auto)
		
		
		if(ret == None):
			print("No articles detected, SALTbot will not introduce anything to wikidata")
		else: 
			if(ret[1]!=None):
				aux = print_links(ret[0], ret[1], ret[2])
				if aux != None:
					operation_list.append(aux)
			else:
				site = pywikibot.Site("test", "wikidata")

				message_summary = u'Creating new software: ' + info['name']['excerpt']
				test_name = "SALTbot test : "+info['name']['excerpt']
				label_dict = {"en": test_name}

				
				if(upload == True):
					new_software = pywikibot.ItemPage(site)

					new_software.editLabels(labels=label_dict, summary=message_summary)

					software_qnode = new_software.getID()
				
					operation_list.append(print_links(ret[0], (software_qnode, test_name), ret[2]))
				else:
					operation_list.append(print_links(ret[0], (None, test_name), ret[2]))
			
			


		
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
			filename = o.path.replace("/", " ").split()[1] + ".json"
			print("filename: ", filename)

			print("somef describe -r ",i," -o "+filename+" -t 0.8")
			os.system("somef describe -r "+i+" -o "+filename+" -t 0.8")

			try:
				f = open(filename,"r")
			except:
				print("SALTbot ERROR: no files")
			
			info = json.loads(f.read())
			ret = SALTbot(info, keyword, auto)


			if(ret == None):
				print("No articles detected, SALTbot will not introduce anything to wikidata")
			else: 
				if(ret[1]!=None):
					aux = print_links(ret[0], ret[1], ret[2])
					if aux != None:
						operation_list.append(aux)
				else:
					#create articulo
					#operation_list.append(print_links(ret[0], ret[1], ret[2]))
					pass
			

	elif(jsondir):
		

		alljsons = jsondir+'/*.json'

		for jsonfile in glob.glob(alljsons):
			
			print()
			operation = "JSONFILE: " + jsonfile
			click.echo(click.style(operation, fg='yellow', bold=True))

			f = open(jsonfile, 'r')
			info = json.loads(f.read())
			ret = SALTbot(info, keyword, auto)


			if(ret == None):
				print("No articles detected, SALTbot will not introduce anything to wikidata")
			else: 
				if(ret[1]!=None):
					aux = print_links(ret[0], ret[1], ret[2])
					if aux != None:
						operation_list.append(aux)
				else:
					#create articulo
					#operation_list.append(print_links(ret[0], ret[1], ret[2]))
					pass
		
	if(operation_list!=[]):
			print()
			click.echo(click.style('SALTbot WILL INTRODUCE THIS STATEMENTS IN WIKIDATA', fg='red', bold = True))
			for i in operation_list:
				for j in i:
					if j[1]=='P921':
						print("| ARTICLE:  ", j[0][0]," : ", j[0][1], " | PROPERTY: ", j[1], " : main_subject | SOFTWARE: ", j[2][0], " : ", j[2][1], " |")
					elif j[1]=='P1343':
						print("| SOFTWARE:  ", j[0][0]," : ", j[0][1], " | PROPERTY: ", j[1], " : described_by_source | ARTICLE: ", j[2][0], " : ", j[2][1], " |")

					
			
			print()
			confirmation = input("CONFIRM (Y/N): ").strip()

			while(confirmation != "Y" and confirmation != "N"):
				confirmation = input("ONLY Y OR N ARE VALID CONFIRMATION ANSWERS. CONFIRM (Y/N): ").strip()	

			if(confirmation == "Y" and upload == True):
				site = pywikibot.Site("test", "wikidata")
				for i in operation_list:
					for j in i:
						if(j[1]=='P1343'):
							article_repo = site.data_repository()
							article_page = pywikibot.ItemPage(article_repo, qnode_software_test)
							article_no_claim = article_page.get()
							article_claim = pywikibot.Claim(article_repo, described_by_source_test) 				#Adding described_by_source property
							article_target = pywikibot.ItemPage(article_repo, qnode_article_test) 			#linking article with software
							article_claim.setTarget(article_target) 												#Set the target value in the local object.

							message_summary = u'Adding claim described_by_source ' + str(qnode_article_test) +u' to entity ' + str(qnode_software_test)

							print(message_summary)
							article_page.addClaim(article_claim, summary=message_summary) 
						
						elif(j[1]=='P921'):

							article_repo = site.data_repository()
							article_page = pywikibot.ItemPage(article_repo, qnode_article_test)
							article_no_claim = article_page.get()
							article_claim = pywikibot.Claim(article_repo, main_subject_test) 				#Adding main_subject property
							article_target = pywikibot.ItemPage(article_repo, qnode_software_test) 	#linking article with software
							article_claim.setTarget(article_target) 												#Set the target value in the local object.

							message_summary = u'Adding claim main_subject ' + str(qnode_software_test) +u' to entity ' + str(qnode_article_test)

							print(message_summary)
							article_page.addClaim(article_claim, summary=message_summary) 							#Inserting value with summary to article


		
	




		



if(__name__=='__main__'):
	main()
