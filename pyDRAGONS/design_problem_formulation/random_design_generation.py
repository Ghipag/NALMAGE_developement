import rdflib
import py2neo
import pprint
import database_interaction.database_tools as database_tools
import random
import re
import time
import database_interaction.data_extraction as data_extraction
import interface
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
import json 
import design_problem_formulation.design_problem_query_tools as design_problem_query_tools

def generate_design_element(name,labels:dict,root_element_info:dict,design_name,variability_framework,graph):
  # construct element name and check for uniqueness constraint
  if 'unique_in_design' not in design_problem_query_tools.identify_element_constraints(labels,variability_framework):
    design_element_name = design_name+'_'+name
  else:
    # if the element should be unique, then identify if pre-existing version exists and select this
    # or generate new one
    query = """
                    MATCH (element:"""+labels['classifier']+""")
                    Return element
                """
    reponse = database_tools.run_neo_query(['nil'],query,graph)
    if reponse:
      design_element_name = reponse[0]['element']['uid']
    else:
      design_element_name = design_name+'_'+name
  print(f'element to be "generated" is {design_element_name}')


  #construct superclass list string 
  superclass_string = ''
  for label in labels['superclasses']:
    superclass_string = superclass_string +':'+label
  if root_element_info:
    if (root_element_info['relationship_direction'] == 'INCOMING') & ('Comparison' not in labels['classifier']) & ('Difference' not in labels['classifier']):
      query = """
                    MATCH (root_element:"""+design_name+"""_Design_Instance_Element {uid: '"""+root_element_info['root_element']+"""'})
                    MERGE (element:"""+design_name+"""_Design_Instance_Element {uid: '"""+design_element_name+"""'})-[:"""+root_element_info['relationship_type']+"""]->(root_element)
                    SET 
                        element:Design_Element"""+superclass_string+""",
                        element:"""+ labels['classifier'] +""",
                        element.name = '"""+ name +"""',
                        element.Classifier = '"""+ labels['classifier'] +"""',
                        element.Multiplicity = """+ str(labels['multiplicity']) +"""
                """
      print(query)
      print(f' root info: {root_element_info}')
      database_tools.run_neo_query(['nil'],query,graph)
    elif (root_element_info['relationship_direction'] == 'OUTGOING') & ('Comparison' not in labels['classifier']) & ('Difference' not in labels['classifier']):
      query = """
                    MATCH (root_element:"""+design_name+"""_Design_Instance_Element {uid: '"""+root_element_info['root_element']+"""'})
                    MERGE (element:"""+design_name+"""_Design_Instance_Element {uid: '"""+design_element_name+"""'})<-[:"""+root_element_info['relationship_type']+"""]-(root_element)
                    SET 
                        element:Design_Element"""+superclass_string+""",
                        element:"""+ labels['classifier'] +""",
                        element.name = '"""+ name +"""',
                        element.Classifier = '"""+ labels['classifier'] +"""',
                        element.Multiplicity = """+ str(labels['multiplicity']) +"""
                """
      print(query)
      print(f' root info: {root_element_info}')
      database_tools.run_neo_query(['nil'],query,graph)
  else:
    query = """
                MERGE (element:"""+design_name+"""_Design_Instance_Element {uid: '"""+design_element_name+"""'})
                SET 
                    element:Design_Element"""+superclass_string+""",
                    element:"""+ labels['classifier'] +""",
                    element.name = '"""+ name +"""',
                    element.Classifier = '"""+ labels['classifier'] +"""',
                    element.Multiplicity = """+ str(labels['multiplicity']) +"""
            """
    print(query)
    print(f' root info: {root_element_info}')
    database_tools.run_neo_query(['nil'],query,graph)

  return design_name+'_'+name


def generate_neighbours(allowed_neighbours,root_element,design_name,design_graph,variability_framework):
  global no_complete_generations

  # generate neighbours from incoming allowed relations
  for elememt_type in allowed_neighbours['incoming']:
    root_element_info = {'root_element':root_element,'relationship_type':elememt_type[0],'relationship_direction':'INCOMING'}
    labels = {'classifier':elememt_type[1],'multiplicity':1,'superclasses': []}
    
    # check sub and super classes
    superclass_list, subclass_list = design_problem_query_tools.identify_child_types(labels,variability_framework)

    root_element_info = {'root_element':root_element,'relationship_type':elememt_type[0],'relationship_direction':'INCOMING'}
    labels['superclasses'] = superclass_list

    # use confidence to decide to generate this child
    rng_val = random.random()/1000
    comp_val = elememt_type[2]
    if (float(rng_val) <= float(comp_val)) and design_problem_query_tools.check_for_relevant_type(labels,root_element_info) and not subclass_list and (no_complete_generations < max_generations) :
      print(f'generating candidate {elememt_type[1]}')
      print(f'on generation {no_complete_generations}')
      print(f'parent element: {root_element}')
      no_complete_generations += 1
      child_uid = generate_design_element('element_'+str(no_complete_generations),labels,root_element_info,design_name,variability_framework,design_graph)
      allowed_child_neighbours = identify_candidate_neighbours(elememt_type[1],variability_framework,True)
      generate_neighbours(allowed_child_neighbours,child_uid,design_name,design_graph,variability_framework)
      
  # generate neighbours from outgoing allowed relations
  for elememt_type in allowed_neighbours['outgoing']:
    root_element_info = {'root_element':root_element,'relationship_type':design_problem_query_tools.process_uriref_string(elememt_type[0]),'relationship_direction':'OUTGOING'}
    labels = {'classifier':elememt_type[1],'multiplicity':1,'superclasses': superclass_list}
    if check_for_relevant_type(labels,root_element_info) and not subclass_list and (no_complete_generations < max_generations):
      print(f'generating candidate {elememt_type[1]}')
      print(f'on generation {no_complete_generations}')
      print(f'parent element: {root_element}')
      no_complete_generations += 1
      child_uid = generate_design_element('element_'+str(no_complete_generations),{'classifier':elememt_type[1],'multiplicity':1},root_element_info,design_name,variability_framework,design_graph)
      allowed_child_neighbours = design_problem_query_tools.identify_candidate_neighbours(elememt_type[1],variability_framework,True)
      generate_neighbours(allowed_child_neighbours,child_uid,design_name,design_graph,variability_framework)

def generate_random_design(variability_framework,design_graph):
  # start with root spacecraft node, display design options
  design_name = 'test_design'
  element_type = 'Spacecraft'
  root_name = 'my_Spacecraft'
  labels = {'classifier':element_type,'multiplicity':1,'superclasses':[]}
  root_element = design_name+'_'+root_name

  superclass_list, subclass_list = design_problem_query_tools.identify_child_types(labels,variability_framework)
  labels['superclasses'] = superclass_list

  generate_design_element(root_name,labels,{},design_name,variability_framework,design_graph)

  allowed_neighbours = design_problem_query_tools.identify_candidate_neighbours(element_type,variability_framework,True)
  print(allowed_neighbours)

  # now recursively generate neighbours
  generate_neighbours(allowed_neighbours,root_element,design_name,design_graph,variability_framework)
   