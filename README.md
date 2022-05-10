# SALTbot: Software and Article Linker Toolbot


## DESCRIPCIÓN

  Este repositorio contiene la implementación de un bot capaz de enlazar Articulos Cientificos y su implementación Software en Wikidata

## INSTALACIÓN

  Es necesario disponer de un entorno con Python 3.9 y la herramienta SOMEF (https://github.com/KnowledgeCaptureAndDiscovery/somef) antes de ejecutar el script

## USO

  ### **./main URL** 
  
  El script descargará los metadatos del repositorio con SOMEF y comenzará la ejecución
  
  ### **./main -i FICHERO.json**
  
  Si los metadatos del repositorio ya están descargados en un fichero JSON se puede pasar como parámetro para no tener que extraer los metadatos
  