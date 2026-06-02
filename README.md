**# AGENTS-LEAGUE-HACKATHON-2026

Base Prototype File Arquitecture

###  Containers ENV
Aqui es donde se encontraran la sespecificaciones de deployment de los contenedores externos como las base de datos y otros este no es algo que se va a acceder atraves de los archivos externos estos son archivos que estar an primeramente en la nube deploados usando octopus deployment

25gb de Espacio
Lo mejor es solo usar octopus para acceso y alamcenamiento de datos no para ningun otro componente extra

###  Data Ingestor
Demographic Data:  Data Commons resource: https://datacommons.org/place/geoId/3651000
Apps 

Aqui es donde estaran los scripts para la ingestra de nuestros datos creados de forma artificial apartir de datos estadisticos de diferentese fuentes de informacion en donde se ordenaran y haran los perfiles de audiencia generalizado

La "Audiencia" no son personas especcificas son grupos agrupudas por compartamientos estadisticos

###  Data Processor
Aqui se procesara la data cruda es un sdcript inicial para generar los datos necesarios para el data ingestor

###  DTOS
Lo mejor es crear DTOs para el manejo de toda esta data para no perderse entre el codigo

###  UI OnLooker
Aqui es donde entrara el usaurio para interactuar con el sistema y ver resultados

