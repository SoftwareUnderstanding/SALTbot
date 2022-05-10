#!/home/jorge/TFG/TFGenv/bin/python
import json
import os
import sys
from urllib.parse import urlparse
import yaml
from yaml.loader import SafeLoader
import bibtexparser
import requests
import time
import click
from datetime import datetime

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
			enlace_articulo_software = 1

	except:
		pass
	try:
		if Qnode_s in enlaces_Articulo[Qnode_a]:
			enlace_software_articulo = 1
	except:
		pass

	return (enlace_articulo_software, enlace_software_articulo)


@click.command()
@click.option('--auto', '-a', is_flag=True, help='sets bot to auto mode')
@click.option('--jsonfile','-js', default=None, type = click.Path(exists=True), help='JSON extracted from the repository with SOMEF')
@click.option('--keyword', '-k', default = None, help = 'Keyword for searching in case no articles or software were found')
@click.option('--url', '-u', default = None, help = 'repository url')
@click.option('--csvfile','-csv', default=None, type = click.Path(exists=True), help='.csv file with one or more entries and format \n {URL,KEYWORD}')
@click.option('--jsondir', '-dir', default = None, type = click.Path(exists=True), help = 'Path of a directory with one or multiple JSONs extracted with SOMEF')

def main(auto, jsonfile, keyword, url, csvfile, jsondir):

	if(jsonfile != None and url == None and csvfile == None and jsondir == None):
		print("--------------------------------------------FILE: ",jsonfile,"--------------------------------------------")
		try:
			f = open(jsonfile, 'r')
		except:
			sys.exit("SALTbot ERROR: Path provided as JSON file parameter is invalid")

	elif(jsonfile == None and url != None and csvfile == None and jsondir == None):
		print("--------------------------------------------URL: ",url,"--------------------------------------------")
		now = datetime.now().time()
		fich = str(now).replace(":", "") + ".json"
		os.system("somef describe -r "+url+" -o "+fich+" -t 0.8")
		try:
			f = open(fich,"r")
		except:
			sys.exit("SALTbot ERROR: url is not a valid repository")
	elif(jsonfile == None and url == None and csvfile != None and jsondir == None):
		pass
	elif(jsonfile == None and url == None and csvfile == None and jsondir != None):
		pass
	else:
		sys.exit("SALTbot ERROR: Provide at least one and only one of the following parameters: \n --jsonfile \n --url \n --csvfile \n --jsondir")


	#Se pasa el fichero a JSON
	info = json.loads(f.read())

	parsedinfo = []

	pag_articulo = False
	pag_software = False
	enlace_readme_articulo = False
	enlace_articulo_software = False
	enlace_software_articulo = False

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




	# si se ha encontrado al menos un titulo
	if(parsedinfo != []):

		#Por cada titulo
		for i in parsedinfo:

			#si es BIB
			if(i[0]=="BIB"):

				#Se imprime el titulo
				try:
					print("TITULO DETECTADO: ", i[1].entries[0]["title"], "     ", "TECNICA EMPLEADA: ", i[2], "     ", "PARSING: ", i[0])

				#si el archivo se ha parseado mal se elimina
				except:
					parsedinfo.remove(i)

			#si es YAML
			elif(i[0]=="YAML"):

				#Se imprime el titulo
				try:
					print("TITULO DETECTADO: ", i[1]["title"], "     ", "TECNICA EMPLEADA: ", i[2],"     ", "PARSING: ", i[0])

				#si el archivo se ha parseado mal se elimina
				except:
					parsedinfo.remove(i)


	#Si no se encuentran titulos
	else:
		print("TITULOS NO DETECTADOS")


	#url = 'https://query.wikidata.org/sparql'
	url = 'https://query.wikidata.org/sparql'
	set_articulos = {}
	set_softwares = {}


	#por cada elemento en la lista de titulos
	for i in parsedinfo:

		#si es repository name se añade el titulo
		if(i[0]=="REPOSITORY NAME"):
			concat_query = i[1]

		#si es BIB se extrae del bibtex
		elif(i[0] == "BIB"):
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




	#So ha encontrado al menos una entidad a partir de los datos parseados
	if(set_articulos != {}):
		#Existe la pagina del articulo en WikiData
		pag_articulo = True

		#Existe un enlace desde el repositorio hasta el articulo en Wikidata
		enlace_readme_articulo = True


	#Si no ha encontrado nada
	else:
		print("NO SE HAN DETECTADO ARTICULOS - SE PRUEBA CON API")

		#Se buscan todos los articulos a partir del nombre del repositorio
		set_articulos = getEntitiesByName(url, info['name']['excerpt'], 0)
		time.sleep(1)

		#si buscando el repositorio se ha encontrado al menos un articulo existe pagina de articulo
		if(set_articulos!={}):
			pag_articulo = True



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



	#Si se ha encontrado al menos un enlace articulo-software
	if(enlaces_articulo_software != {}):

		#existe la pagina de software
		pag_software = True

		#existe el enlace articulo-software
		enlace_articulo_software = True

	#si no se ha encontrado ningun software enlazado
	else:
		print("NO SE HAN DETECTADO SOFTWARES - SE PRUEBA CON API")

		#se buscan todos los softwares a partir del nombre del repositorio
		set_softwares = getEntitiesByName(url, info['name']['excerpt'], 1)

		time.sleep(1)

		#si se ha encontrado al menos un software
		if(set_softwares!={}):

			#existe la pagina de software
			pag_software = True

	#comprobar enlaces_completos

	#por cada software
	for i in set_softwares:
		#se buscan los articulos enlazados
		result_articulo = articulosEnlazados(url, i)
		time.sleep(1)

		if(result_articulo != {}):
			enlaces_software_articulo.update({i:result_articulo})

	if(enlaces_software_articulo != {}):
		enlace_software_articulo=True


	print("\n")
	print("RESULTADOS ENCONTRADOS: ")
	print("\n")
	print("ARTICULOS: ")
	for i in set_articulos:
		print(i, " : ", set_articulos[i])

	print("\n")
	print("SOFTWARES: ")
	for i in set_softwares:
		print(i, " : ", set_softwares[i])

	print("\n")
	print("CLASIFICACION")
	print("\n")
	#print("pag_software: ", pag_software)
	#print("pag_articulo: ", pag_articulo)
	#print("enlace_readme_articulo: ", enlace_readme_articulo)
	#print("enlace_articulo_software", enlace_articulo_software)
	#print("enlace_software_articulo", enlace_software_articulo)
	print("enlaces articulo-software", enlaces_articulo_software)
	print("enlaces software-articulo", enlaces_software_articulo)
	print("\n")



	if(set_articulos != {} and set_softwares != {}):

		print("ENLAZAMIENTO")
		print("\n")
		contador = 0
		map_articulos = {}
		print("SELECCIONE UN ARTICULO: ")
		for i in set_articulos:
			contador = contador + 1
			print(contador, " - ", i, " : ", set_articulos[i])
			map_articulos.update({str(contador):i})




		inp_articulo = input("NUMERO ARTICULO: ").strip()

		while(inp_articulo not in map_articulos):
			inp_articulo = input("NO ES UN ARTICULO VALIDO. SELECCIONE OTRO: ").strip()


		contador = 0
		map_softwares = {}
		print("SELECCIONE UN QNODE DE SOFTWARE: ")
		for i in set_softwares:
			contador = contador + 1
			print(contador, " - ", i, " : ", set_softwares[i])
			map_softwares.update({str(contador):i})


		inp_software = input("NUMERO SOFTWARE: ").strip()

		while(inp_software not in map_softwares):
			inp_software = input("NO ES UN SOFTWARE VALIDO. SELECCIONE OTRO: ").strip()


		print("QNODEART: ", map_articulos[inp_articulo])
		print("QNODEsoft: ", map_softwares[inp_software])
		res = checkEnlaces(enlaces_articulo_software, enlaces_software_articulo, map_articulos[inp_articulo], map_softwares[inp_software])

		#print(res[0], res[1])

		if(res[0]==0):
			print("enlazar inp_articulo main_subject inp_software")

		else:
			print("articulo ya enlazado con software")
		if(res[1]==0):
			print("enlazar inp_software described_by_source inp_articulo")

		else:
			print("software ya enlazado con articulo")

if(__name__=='__main__'):
	main()
