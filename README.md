# DRAGONS-development
This repository contains all the code and related data for performing generative design of system architectures using LLM's and the DRAGONS architecting method, also presented [in this repo](https://github.com/Ghipag/DRAGONS-development/tree/main). Documentation may be found (in HTML format, should be viewed in a browser) under \docs. The architecture data used to run experiments is stored under /data.

## Setup
A [Neo4j](https://neo4j.com/) graph database was used to handle the model data and was setup to run inside a [docker container](https://neo4j.com/docs/operations-manual/current/docker/). The python package [py2neo](https://py2neo.org/2021.1/) was used as an interface between the database and python. An OpenAI API key was used to make calls to their various LLM models, and should be stored separately to this repository.
