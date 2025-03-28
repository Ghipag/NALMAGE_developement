from pyDRAGONS.design_problem_formulation import design_problem_query_tools
from pyDRAGONS.database_interaction.data_extraction import data_extraction
from pyDRAGONS.variability_framework_tools.variability_framework_compliance_testing import variability_framework_compliance_testing
from pyDRAGONS.database_interaction.database_tools import database_tools
from distutils.dir_util import copy_tree
from pyDRAGONS.interface.interface import interface
import load_designs
import variability_framework_identifacation
import time
import subprocess
import os
from py2neo import Graph
import rdflib
import json
from tqdm import tqdm
import main

#####################################################################
# This module provides tools for testing collected differences 
# against a particular variability framework (or set of conditions)
# or identifying that variability framework
#####################################################################

def list_names_of_element_type(requested_type,graph):
    query = """
                MATCH(n:"""+requested_type+""") RETURN n
            """
    response = database_tools.run_neo_query(['nil'],query,graph)
    type_names = []
    for entry in response:
        type_names.append(entry['n']['name'])

    return type_names

def filter_for_included_references(unfiltered_temp_data):
    temp_data = unfiltered_temp_data.copy()
    ignore_indexes = ['name', 'classifier','parameter_value', 'multiplicity', 'sub_class', 'related_signal', 'related_requirement']
    names = temp_data['name'].to_list()
    #print(names)

    for index, row in temp_data.items():
        if not index in ignore_indexes:
            for k, references in row.items():
                references_copy = references
                #print(f'references are: {references}')
                for reference in references.split(';'):
                    if not reference == 'NONE' and not reference in names:
                        #print(f'correcting: {k,reference,index}')
                        # need a bit of logic to ensure correct ; positioning
                        if references_copy.startswith(reference):
                            references_copy = references_copy.replace(reference+';','',1)
                        elif references_copy.endswith(reference):
                            references_copy = references_copy.replace(';'+reference,'')
                        else:
                            references_copy = references_copy.replace(';'+reference+';',';')
                            #if references_copy[0] ==';':
                            #    references_copy = references_copy[1:]
                        if len(references_copy.split(';')) > 1:
                            temp_data.loc[k,index] = references_copy
                        else:
                            temp_data.loc[k,index] = 'NONE'
    return temp_data

def correct_uid_and_type(temp_name,meta_type,graph):
    query = """
                MATCH (temp_element:Temp_Type:"""+temp_name+"""_Design_Instance_Element)
                RETURN temp_element
                """
    response = database_tools.run_neo_query(['nil'],query,graph)
    for entry in response:
        query = """
                MATCH (temp_element:"""+temp_name+"""_Design_Instance_Element {name:'"""+entry['temp_element']['name']+"""'})
                SET temp_element.uid = '"""+temp_name+entry['temp_element']['name']+"""',
                    temp_element:"""+meta_type+"""
                REMOVE temp_element:Temp_Type
                """
        database_tools.run_neo_query(['nil'],query,graph)

def copy_over_labels(labels_response,temp_name,design_name,graph):
    for entry in labels_response:
        label_str = ''
        for label in entry['labels']:
            # some filtering for relevant labels only
            if not label == 'NONE' and not 'Valid_ALLOWED' in label:
                label_str = label_str + ':' + label
        label_str = label_str[1:]
        query = """
                    MATCH (new_source:"""+temp_name+"""_Design_Instance_Element {name:'"""+entry['name']+"""'})
                    SET new_source:"""+ label_str +"""
                    REMOVE new_source:"""+ design_name +"""_Design_Instance_Element
                    """
        database_tools.run_neo_query(['nil'],query,graph)

def grab_design_section(transaction_id,temp_name,design_name,meta_type,grab_relationship_type,root_element,graph):
    if meta_type == 'Spacecraft':
        query = """
                MATCH (og_source:"""+design_name+"""_Design_Instance_Element {name:'"""+root_element+"""'})
                CREATE (new_source:Temp_Type:"""+temp_name+"""_Design_Instance_Element)
                SET new_source = og_source,
                    new_source:Transaction_"""+str(transaction_id)+"""
                RETURN og_source.name as name, labels(og_source) as labels
                """
        response = database_tools.run_neo_query(['nil'],query,graph)
    else:
        
        query = """
                MATCH (new_source:"""+temp_name+"""_Design_Instance_Element {name:'"""+root_element+"""'})
                WITH new_source
                MATCH (og_source:"""+design_name+"""_Design_Instance_Element {uid:'"""+design_name+root_element+"""'})<-[og_r:"""+grab_relationship_type+"""]-(og_target:"""+meta_type+""":"""+design_name+"""_Design_Instance_Element)
                MERGE (new_target:"""+temp_name+"""_Design_Instance_Element  {name:og_target.name})
                ON CREATE
                    SET new_target:Temp_Type,
                        new_target = og_target
                MERGE (new_source)<-[new_r:"""+grab_relationship_type+"""]-(new_target)
                SET new_target:Transaction_"""+str(transaction_id)+"""
                RETURN og_target.name as name, labels(og_target) as labels
                """
        response = database_tools.run_neo_query(['nil'],query,graph)

    # need to correct uid's
    correct_uid_and_type(temp_name,meta_type,graph)
    copy_over_labels(response,temp_name,design_name,graph)
    transaction_id += 1
    return transaction_id

def grab_design_section_dataframe_based(design_data,temp_data_unfiltered,mission_name,design_name,meta_type,grab_relationship_types,root_element,graph):
    temp_data_original = temp_data_unfiltered.copy()
    grab_element_types = return_types(meta_type,graph)

    for index, row in design_data.iterrows():
        if not root_element and row['classifier'] == 'Spacecraft':
            temp_data_unfiltered.loc[len(temp_data_unfiltered.index)] = row
            temp_data = filter_for_included_references(temp_data_unfiltered)
        else:
            if grab_element_types and row['classifier'] in grab_element_types:
                temp_data_unfiltered.loc[len(temp_data_unfiltered.index)+1] = row
                temp_data = filter_for_included_references(temp_data_unfiltered)

    # now clean database and load section into database
    #database_tools.clear_database_by_label(graph,design_name+"_Design_Instance_Element")
    data_extraction.process_design_data(mission_name,design_name,temp_data,graph)
    return temp_data,temp_data_unfiltered,temp_data_original

def return_types(meta_type,graph):
    if meta_type == 'Spacecraft':
        grab_element_types = ['Spacecraft']
    else:
        query = """
                MATCH(n:"""+meta_type+"""_Classifier) RETURN n
            """
        response = database_tools.run_neo_query(['nil'],query,graph)
        grab_element_types = []
        for entry in response:
            grab_element_types.append(entry['n']['name'])
    print(grab_element_types)
    return grab_element_types

def calculate_precision_recall(grab_element_results,query_returned_results):
    grab_set = set(grab_element_results)
    query_set = set(query_returned_results)

    print(f'grab set:{grab_set}')
    print(f'query set: {query_set}')

    intersection = grab_set.intersection(query_set)

    if len(query_set) == 0:
        precision = 0
    else:
        precision = len(intersection)/len(query_set)
    if len(grab_set) == 0:
        recall = 0
    else:
        recall = len(intersection)/len(grab_set)

    return precision,recall,grab_set,query_set

def aggregate_results(results):
    precision_list = []
    recall_list = []
    elements_of_concern = []
    results_per_query_type = {'r2f':{'average_precision':0,'average_recall':0,'results':{'precision':[],'recall':[]}},
                              'f2m':{'average_precision':0,'average_recall':0,'results':{'precision':[],'recall':[]}},
                              'f2c':{'average_precision':0,'average_recall':0,'results':{'precision':[],'recall':[]}},
                              'c2c':{'average_precision':0,'average_recall':0,'results':{'precision':[],'recall':[]}}}
    results_per_relationship_type = {}
    for design_variable_key in results.keys():
            for relationship_type_key in results[design_variable_key].keys():
                if not relationship_type_key in results_per_relationship_type.keys():
                    results_per_relationship_type[relationship_type_key] = {'average_precision':0,'average_recall':0,'results':{'precision':[],'recall':[]}}
                for transaction_key in results[design_variable_key][relationship_type_key].keys():
                    transaction = results[design_variable_key][relationship_type_key][transaction_key]
                    if not len(transaction['grab_set']) == 0 :
                        #not(transaction['recall'] == 0 and transaction['precision'] == 0):#
                        precision_list.append(transaction['precision'])
                        recall_list.append(transaction['recall'])
                        if transaction_key == 'transaction_2':
                            query_type_key = 'r2f'
                        elif transaction_key == 'transaction_3':
                            query_type_key = 'f2c'
                        elif transaction_key == 'transaction_4':
                            query_type_key = 'f2m'
                        else:
                            query_type_key = 'c2c'    
                        results_per_query_type[query_type_key]['results']['precision'].append(transaction['precision'])
                        results_per_query_type[query_type_key]['results']['recall'].append(transaction['recall'])
                        results_per_relationship_type[relationship_type_key]['results']['precision'].append(transaction['precision'])
                        results_per_relationship_type[relationship_type_key]['results']['recall'].append(transaction['recall'])
                        if transaction['recall'] == 0:
                            elements_of_concern.append([design_variable_key,relationship_type_key,transaction])
                    # set conversion
                    results[design_variable_key][relationship_type_key][transaction_key]['grab_set'] = list(results[design_variable_key][relationship_type_key][transaction_key]['grab_set'])
                    results[design_variable_key][relationship_type_key][transaction_key]['query_set'] = list(results[design_variable_key][relationship_type_key][transaction_key]['query_set'])
                    

    # calculating averages
    average_precision = sum(precision_list)/len(precision_list)
    average_recall = sum(recall_list)/len(recall_list)

    #print(results_per_relationship_type)
    # now aggregate over types
    for relationship_type in results_per_relationship_type.keys():
        if not len(results_per_relationship_type[relationship_type]['results']['precision']) == 0:
            results_per_relationship_type[relationship_type]['average_precision'] = sum(results_per_relationship_type[relationship_type]['results']['precision'])/len(results_per_relationship_type[relationship_type]['results']['precision'])
            results_per_relationship_type[relationship_type]['average_recall'] = sum(results_per_relationship_type[relationship_type]['results']['recall'])/len(results_per_relationship_type[relationship_type]['results']['recall'])
        else: 
            results_per_relationship_type[relationship_type]['average_precision'] = 'NO TEST'
            results_per_relationship_type[relationship_type]['average_recall'] = 'NO TEST'
    for query_type in results_per_query_type.keys():
        if not len(results_per_query_type[query_type]['results']['precision']) == 0:
            results_per_query_type[query_type]['average_precision'] = sum(results_per_query_type[query_type]['results']['precision'])/len(results_per_query_type[query_type]['results']['precision'])
            results_per_query_type[query_type]['average_recall'] = sum(results_per_query_type[query_type]['results']['recall'])/len(results_per_query_type[query_type]['results']['recall'])
        else: 
            results_per_query_type[query_type]['average_precision'] = 'NO TEST'
            results_per_query_type[query_type]['average_recall'] = 'NO TEST'
    #print(f'average precision:{average_precision}')
    #print(f'average recall: {average_recall}')
    return average_precision,average_recall,elements_of_concern,results_per_relationship_type,results_per_query_type

def test_justification(transaction_id,meta_type,grab_relationship_types,temp_name,design_data,requirement_names,dependant_variable_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph):
    skip =  False
    # dirty solution to skip test section
    if skip:
        for grab_relationship_type in grab_relationship_types:
            transaction_id = grab_design_section(transaction_id,temp_name,design_name,meta_type,grab_relationship_type,root_element_name,graph)
            return results,transaction_id
    
    # cleaning database of original design data to avoid confusion over elements related to requirements
    database_tools.clear_database_by_label(graph,design_name+"_Design_Instance_Element")

    if step_type == 'Internal Interfaces Analysis':
        # need to relabel all existing component interfaces to avoid missing query results
        database_tools.relabel_design_relationships('POWER_INTERFACE','UNCONFIRMED_POWER_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('DATA_INTERFACE','UNCONFIRMED_DATA_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('MECHANICAL_INTERFACE','UNCONFIRMED_MECHANICAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('THERMAL_INTERFACE','UNCONFIRMED_THERMAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('FLUID_INTERFACE','UNCONFIRMED_FLUID_INTERFACE',temp_name,graph)

    # first constructing query 
    design_query = {'query type':step_type,'requirement':requirement_names,'design variable':[root_element_name],'dependant variable':dependant_variable_names,'additional model elements':[]}

    # running query
    completed_query = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,temp_name,graph)

    if step_type == 'Internal Interfaces Analysis':
        # now need to relabel previously relabelled interfaces
        database_tools.relabel_design_relationships('UNCONFIRMED_POWER_INTERFACE','POWER_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_DATA_INTERFACE','DATA_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_MECHANICAL_INTERFACE','MECHANICAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_THERMAL_INTERFACE','THERMAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_FLUID_INTERFACE','FLUID_INTERFACE',temp_name,graph)

    # adding actual model elements
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    # need to loop through each relevant relationship type
    if not root_element_name in results:
        results[root_element_name] = {}
    for grab_relationship_type in grab_relationship_types:
        if not grab_relationship_type in results[root_element_name]:
            results[root_element_name][grab_relationship_type] = {}
        transaction_id = grab_design_section(transaction_id,temp_name,design_name,meta_type,grab_relationship_type,root_element_name,graph)
        
        # return list of grabbed type labels
        if step_type == 'Internal Interfaces Analysis':
            grab_element_results = []
            query = """
                MATCH(n:"""+temp_name+"""_Design_Instance_Element:Transaction_"""+str(transaction_id-1)+""") RETURN n
            """
            response = database_tools.run_neo_query(['nil'],query,graph)
            for entry in response:
                grab_element_results.append(grab_relationship_type+'/'+entry['n']['name'])
        else:
            query = """
                MATCH(n:"""+temp_name+"""_Design_Instance_Element:Transaction_"""+str(transaction_id-1)+""") RETURN labels(n) AS labels
            """
            response = database_tools.run_neo_query(['nil'],query,graph)
            grab_element_results = []
            grab_element_types_unfiltered = []
            for entry in response:
                for label in entry['labels']:
                    if not label == 'Temp_Type' and not label == 'Design_Element' and not 'Transaction' in label and not temp_name+'_Design_Instance_Element' in label:
                        grab_element_types_unfiltered.append(label)
                        
            # now filter for specific types
            for element_type in grab_element_types_unfiltered:
                labels = {'classifier':element_type,'multiplicity':1,'superclasses': []}
                superclass_list, subclass_list, circular_detected = design_problem_query_tools.identify_child_types(labels,variability_framework,False)
                if not subclass_list:
                    grab_element_results.append(grab_relationship_type+'/'+element_type)

        # return list of query returned type labels
        query_returned_results = []
        if step_type == 'Internal Interfaces Analysis':
            # finding suggest dependant variable entries
            for des_var_key in completed_query['suggested dependant variable'].keys():
                for dep_var_key in completed_query['suggested dependant variable'][des_var_key]:
                    for interface in completed_query['suggested dependant variable'][des_var_key][dep_var_key]:
                        if interface['relationship'] == grab_relationship_type:
                            query_returned_results.append(grab_relationship_type+'/'+dep_var_key)
        else:
            # finding suggest children entries
            for source_type_key in completed_query['additional model elements']['children']:
                for entry in completed_query['additional model elements']['children'][source_type_key]:
                    query_returned_results.append(grab_relationship_type+'/'+entry['type'])

        # compare results
        # now calculating precision and recall 
        precision, recall, grab_set, query_set = calculate_precision_recall(grab_element_results,query_returned_results)

        print(f'precision: {precision}, recall: {recall}')
        results[root_element_name][grab_relationship_type][f'transaction_{transaction_id-1}'] = {'precision':precision,'recall':recall, 'grab_set':grab_set, 'query_set':query_set}

    return results,transaction_id

def test_llm_output(transaction_id,meta_type,grab_relationship_types,temp_name,design_data,requirement_names,dependant_variable_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph):
    skip =  False
    # dirty solution to skip test section
    if skip:
        for grab_relationship_type in grab_relationship_types:
            transaction_id = grab_design_section(transaction_id,temp_name,design_name,meta_type,grab_relationship_type,root_element_name,graph)
            return results,transaction_id
    
    # cleaning database of original design data to avoid confusion over elements related to requirements
    database_tools.clear_database_by_label(graph,design_name+"_Design_Instance_Element")

    if step_type == 'Internal Interfaces Analysis':
        # need to relabel all existing component interfaces to avoid missing query results
        database_tools.relabel_design_relationships('POWER_INTERFACE','UNCONFIRMED_POWER_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('DATA_INTERFACE','UNCONFIRMED_DATA_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('MECHANICAL_INTERFACE','UNCONFIRMED_MECHANICAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('THERMAL_INTERFACE','UNCONFIRMED_THERMAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('FLUID_INTERFACE','UNCONFIRMED_FLUID_INTERFACE',temp_name,graph)

    # LLM interaction


    if step_type == 'Internal Interfaces Analysis':
        # now need to relabel previously relabelled interfaces
        database_tools.relabel_design_relationships('UNCONFIRMED_POWER_INTERFACE','POWER_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_DATA_INTERFACE','DATA_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_MECHANICAL_INTERFACE','MECHANICAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_THERMAL_INTERFACE','THERMAL_INTERFACE',temp_name,graph)
        database_tools.relabel_design_relationships('UNCONFIRMED_FLUID_INTERFACE','FLUID_INTERFACE',temp_name,graph)

    # adding actual model elements
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    # need to loop through each relevant relationship type
    if not root_element_name in results:
        results[root_element_name] = {}
    for grab_relationship_type in grab_relationship_types:
        if not grab_relationship_type in results[root_element_name]:
            results[root_element_name][grab_relationship_type] = {}
        transaction_id = grab_design_section(transaction_id,temp_name,design_name,meta_type,grab_relationship_type,root_element_name,graph)
        
        # return list of grabbed type labels
        if step_type == 'Internal Interfaces Analysis':
            grab_element_results = []
            query = """
                MATCH(n:"""+temp_name+"""_Design_Instance_Element:Transaction_"""+str(transaction_id-1)+""") RETURN n
            """
            response = database_tools.run_neo_query(['nil'],query,graph)
            for entry in response:
                grab_element_results.append(grab_relationship_type+'/'+entry['n']['name'])
        else:
            query = """
                MATCH(n:"""+temp_name+"""_Design_Instance_Element:Transaction_"""+str(transaction_id-1)+""") RETURN labels(n) AS labels
            """
            response = database_tools.run_neo_query(['nil'],query,graph)
            grab_element_results = []
            grab_element_types_unfiltered = []
            for entry in response:
                for label in entry['labels']:
                    if not label == 'Temp_Type' and not label == 'Design_Element' and not 'Transaction' in label and not temp_name+'_Design_Instance_Element' in label:
                        grab_element_types_unfiltered.append(label)
                        
            # now filter for specific types
            for element_type in grab_element_types_unfiltered:
                labels = {'classifier':element_type,'multiplicity':1,'superclasses': []}
                superclass_list, subclass_list, circular_detected = design_problem_query_tools.identify_child_types(labels,variability_framework,False)
                if not subclass_list:
                    grab_element_results.append(grab_relationship_type+'/'+element_type)

        # return list of query returned type labels
        query_returned_results = []
        if step_type == 'Internal Interfaces Analysis':
            # finding suggest dependant variable entries
            for des_var_key in completed_query['suggested dependant variable'].keys():
                for dep_var_key in completed_query['suggested dependant variable'][des_var_key]:
                    for interface in completed_query['suggested dependant variable'][des_var_key][dep_var_key]:
                        if interface['relationship'] == grab_relationship_type:
                            query_returned_results.append(grab_relationship_type+'/'+dep_var_key)
        else:
            # finding suggest children entries
            for source_type_key in completed_query['additional model elements']['children']:
                for entry in completed_query['additional model elements']['children'][source_type_key]:
                    query_returned_results.append(grab_relationship_type+'/'+entry['type'])

        # compare results
        # now calculating precision and recall 
        precision, recall, grab_set, query_set = calculate_precision_recall(grab_element_results,query_returned_results)

        print(f'precision: {precision}, recall: {recall}')
        results[root_element_name][grab_relationship_type][f'transaction_{transaction_id-1}'] = {'precision':precision,'recall':recall, 'grab_set':grab_set, 'query_set':query_set}

    return results,transaction_id

def test_parameter_design_problems_in_design_non_func_reqs(temp_name,design_data,results,mission_name,design_name,variability_framework,graph):
    # parameters stage
    step_type = 'Parametric Analysis'

    # finding all non functional requirements with satisfy relationships
    query = "MATCH(n:Requirement)-[:SATISFY]-(n2) WHERE n.Functional_Non_Functional = 'Non_Functional_Requirement' RETURN n"

    response = database_tools.run_neo_query(['nil'],query,graph)
   
    satisfyable_requirements = []
    satisfyed_requirements = []
    for nf_req_response in response:
        nf_req_name = nf_req_response['n']['name']
        satisfyable_requirements.append(nf_req_name)
        # first constructing query 
        design_query = {'query type':step_type,'requirement':[nf_req_name],'design variable':[],'dependant variable':[],'additional model elements':[]}
        # running query
        completed_query = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,temp_name,graph)

        # now check that a valid parameter design study can be formed
        if completed_query['suggested dependant variable'] and completed_query['suggested design variable']:
            satisfyed_requirements.append(nf_req_name)

    test_result = len(satisfyed_requirements)/len(satisfyable_requirements)
    return {'result':test_result,'satisfyable':satisfyable_requirements,'satisfyed':satisfyed_requirements}

def test_parameter_design_problems_in_design(transaction_id,meta_type,grab_relationship_types,temp_name,design_data,requirement_names,dependant_variable_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph):
    # cleaning database of original design data to avoid confusion over elements related to requirements
    database_tools.clear_database_by_label(graph,design_name+"_Design_Instance_Element")

    # first constructing query 
    if step_type == 'Parametric Analysis':
        design_query = {'query type':step_type,'requirement':requirement_names,'design variable':[],'dependant variable':dependant_variable_names,'additional model elements':[]}

    # running query
    completed_query = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,temp_name,graph)

    # adding actual model elements
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    # need to loop through each relevant relationship type
    if not root_element_name in results:
        results[root_element_name] = {}
    for grab_relationship_type in grab_relationship_types:
        if not grab_relationship_type in results[root_element_name]:
            results[root_element_name][grab_relationship_type] = {}
    
        if step_type == 'Parametric Analysis':
            # grab parameters related to current requirement (root_element), directly from instance design
            grab_element_results = []
            query = """
                MATCH(:"""+mission_name+"""_Requirement_Element {uid:'"""+mission_name+requirement_names[0]+"""'})<-[:"""+grab_relationship_type+"""]-(n:Parameter:"""+design_name+"""_Design_Instance_Element)
                WITH n
                MATCH(n)-[:PARENT]->(parent:"""+design_name+"""_Design_Instance_Element)
                RETURN n,parent
                """
            response = database_tools.run_neo_query(['nil'],query,graph)
            for entry in response:
                grab_element_results.append(grab_relationship_type+"/"+entry['parent']['name']+"/"+entry['n']['Classifier'])

        # return list of query returned type labels
        query_returned_results = []
        if step_type == 'Parametric Analysis':
            # finding suggest dependency entries
            for source_type_key in completed_query['additional model elements']['dependencies']:
                for entry in completed_query['additional model elements']['dependencies'][source_type_key]:
                    # if an owner was identified the there will be a type key
                    if 'type' in entry.keys():
                        for entry_parent_element in entry['suggested parent element']:
                            query_returned_results.append(grab_relationship_type+'/'+entry_parent_element+'/'+entry['type'])

        # compare results
        # now calculating precision and recall 
        precision, recall, grab_set, query_set = calculate_precision_recall(grab_element_results,query_returned_results)

        print(f'precision: {precision}, recall: {recall}')
        results[root_element_name][grab_relationship_type][f'transaction_{transaction_id-1}'] = {'precision':precision,'recall':recall, 'grab_set':list(grab_set), 'query_set':list(query_set)}

    return results,transaction_id

def test_justification_across_design(temp_name,design_name,mission_name,variability_framework,graph):
    results = {}

    # ensure clear database
    database_tools.clear_database(graph)

    # now load classifiers
    # load function classifiers
    function_data = data_extraction.read_data('Functions')
    data_extraction.process_function_classifier_data(function_data,graph)

    # load component classifiers
    component_data = data_extraction.read_data('Components')
    data_extraction.process_component_classifier_data(component_data,graph)
    
    # load Condition classifiers
    condition_data = data_extraction.read_data('Conditions')
    data_extraction.process_condition_classifier_data(condition_data,graph)

    # load mode classifiers
    mode_data = data_extraction.read_data('Modes')
    data_extraction.process_mode_classifier_data(mode_data,graph)

    # load parameter classifiers
    parameter_data = data_extraction.read_data('Parameters')
    data_extraction.process_parameter_classifier_data(parameter_data,graph)

    # load mission requirements
    data_extraction.load_mission_requirements(mission_name,graph)
    requirement_names = list_names_of_element_type('Requirement',graph)

    # load full design data
    design_data = data_extraction.read_data(design_name)
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    
    # now segment design and copy over necessary sections to temp design data frame
    # add root element
    root_element_name = design_data.iloc[0]['name']
    transaction_id = 1
    transaction_id = grab_design_section(transaction_id,temp_name,design_name,'Spacecraft','PARENT',root_element_name,graph)

    # requirement - function stage
    step_type = 'Requirement to Function SA'
    results,transaction_id = test_justification(transaction_id,'Function',['PARENT'],temp_name,design_data,requirement_names,[],step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)

    # function - subsystems stage
    step_type = 'Function to Component SA'
    function_names = list_names_of_element_type('Function',graph)
    results,transaction_id = test_justification(transaction_id,'Subsystem',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)
    
    # function - modes stage
    step_type = 'Function to Mode SA'
    results,transaction_id = test_justification(transaction_id,'Mode',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)
    
    # subsystems - components stage
    step_type = 'Function to Component SA'
    subsystem_names = list_names_of_element_type('Subsystem:'+temp_name+'_Design_Instance_Element',graph)
    for subsystem_name in subsystem_names:
        results,transaction_id = test_justification(transaction_id,'Unit',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,subsystem_name,results,mission_name,design_name,variability_framework,graph)

    # internal interfaces stage
    step_type = 'Internal Interfaces Analysis'
    unit_names = list_names_of_element_type('Unit:'+temp_name+'_Design_Instance_Element',graph)
    for unit_name in unit_names:
        results,transaction_id = test_justification(transaction_id,'Unit',['POWER_INTERFACE','DATA_INTERFACE','MECHANICAL_INTERFACE','FLUID_INTERFACE','THERMAL_INTERFACE'],temp_name,design_data,requirement_names,function_names,step_type,unit_name,results,mission_name,design_name,variability_framework,graph)

    # parameter design cases
    step_type = 'Parametric Analysis'
    parameter_test_results = {}
    for requirement_name in requirement_names:
        # NOTE the spacecraft element is taken as the 'root element' here for the test
        # no design variables are given -> the test is simply a test of the frameworks capability to identify constraints for a parameter design problem
        parameter_test_results,transaction_id = test_parameter_design_problems_in_design(transaction_id,'Parameter',['SATISFY'],temp_name,design_data,[requirement_name],[],step_type,requirement_name,parameter_test_results,mission_name,design_name,variability_framework,graph)
    
    # calculating aggregates and converting sets to lists for result saving
    if results:
        aggregate_results(results)

    with open('test_results/'+mission_name+'_'+design_name+'_'+'justification_test_result.json', 'w') as fp:
        json.dump(results, fp)
    print(parameter_test_results)
    with open('test_results/'+mission_name+'_'+design_name+'_'+'parameter_test_result.json', 'w') as fp:
        json.dump(parameter_test_results, fp)

def test_llm_output_against_design(temp_name,design_name,mission_name,variability_framework,graph):
    results = {}

    # ensure clear database
    database_tools.clear_database(graph)

    # now load classifiers
    # load function classifiers
    function_data = data_extraction.read_data('Functions')
    data_extraction.process_function_classifier_data(function_data,graph)

    # load component classifiers
    component_data = data_extraction.read_data('Components')
    data_extraction.process_component_classifier_data(component_data,graph)
    
    # load Condition classifiers
    condition_data = data_extraction.read_data('Conditions')
    data_extraction.process_condition_classifier_data(condition_data,graph)

    # load mode classifiers
    mode_data = data_extraction.read_data('Modes')
    data_extraction.process_mode_classifier_data(mode_data,graph)

    # load parameter classifiers
    parameter_data = data_extraction.read_data('Parameters')
    data_extraction.process_parameter_classifier_data(parameter_data,graph)

    # load mission requirements
    data_extraction.load_mission_requirements(mission_name,graph)
    requirement_names = list_names_of_element_type('Requirement',graph)

    # load full design data
    design_data = data_extraction.read_data(design_name)
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    
    # now segment design and copy over necessary sections to temp design data frame
    # add root element
    root_element_name = design_data.iloc[0]['name']
    transaction_id = 1
    transaction_id = grab_design_section(transaction_id,temp_name,design_name,'Spacecraft','PARENT',root_element_name,graph)

    # requirement - function stage
    step_type = 'Requirement to Function SA'
    results,transaction_id = test_justification(transaction_id,'Function',['PARENT'],temp_name,design_data,requirement_names,[],step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)

    # function - subsystems stage
    step_type = 'Function to Component SA'
    function_names = list_names_of_element_type('Function',graph)
    results,transaction_id = test_justification(transaction_id,'Subsystem',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)
    
    # function - modes stage
    step_type = 'Function to Mode SA'
    results,transaction_id = test_justification(transaction_id,'Mode',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,root_element_name,results,mission_name,design_name,variability_framework,graph)
    
    # subsystems - components stage
    step_type = 'Function to Component SA'
    subsystem_names = list_names_of_element_type('Subsystem:'+temp_name+'_Design_Instance_Element',graph)
    for subsystem_name in subsystem_names:
        results,transaction_id = test_justification(transaction_id,'Unit',['PARENT'],temp_name,design_data,requirement_names,function_names,step_type,subsystem_name,results,mission_name,design_name,variability_framework,graph)

    # internal interfaces stage
    step_type = 'Internal Interfaces Analysis'
    unit_names = list_names_of_element_type('Unit:'+temp_name+'_Design_Instance_Element',graph)
    for unit_name in unit_names:
        results,transaction_id = test_justification(transaction_id,'Unit',['POWER_INTERFACE','DATA_INTERFACE','MECHANICAL_INTERFACE','FLUID_INTERFACE','THERMAL_INTERFACE'],temp_name,design_data,requirement_names,function_names,step_type,unit_name,results,mission_name,design_name,variability_framework,graph)

    # # parameter design cases
    # step_type = 'Parametric Analysis'
    # parameter_test_results = {}
    # for requirement_name in requirement_names:
    #     # NOTE the spacecraft element is taken as the 'root element' here for the test
    #     # no design variables are given -> the test is simply a test of the frameworks capability to identify constraints for a parameter design problem
    #     parameter_test_results,transaction_id = test_parameter_design_problems_in_design(transaction_id,'Parameter',['SATISFY'],temp_name,design_data,[requirement_name],[],step_type,requirement_name,parameter_test_results,mission_name,design_name,variability_framework,graph)
    
    # calculating aggregates and converting sets to lists for result saving
    if results:
        aggregate_results(results)

    with open('test_results/'+mission_name+'_'+design_name+'_'+'justification_test_result.json', 'w') as fp:
        json.dump(results, fp)
    print(parameter_test_results)
    with open('test_results/'+mission_name+'_'+design_name+'_'+'parameter_test_result.json', 'w') as fp:
        json.dump(parameter_test_results, fp)

def K_fold_testing(missions):

    skip_removes = ['AVDASI_2013_S1', 'AVDASI_2013_S2', 'AVDASI_2017_S1', 'AVDASI_2017_S2', 'AVDASI_2018_S1', 'AVDASI_2018_S2', 'AVDASI_2018_S3', 'AVDASI_2020_S1', 'AVDASI_2020_S2', 'AVDASI_2020_S3', 'AVDASI_2021_S1']
    
    # running through k-groups
    # need to pop out selected design
    for mission_name in tqdm(missions.keys(), colour='green'):
        for design_name_to_remove in missions[mission_name]:
            # method for skipping completed groups
            if not design_name_to_remove in skip_removes:
                # reconstruct missions dict without design to exclude
                missions_k_group = {}
                missions_separated = {}
                for mission_name_rec in missions.keys():
                    missions_k_group[mission_name_rec] = []
                    for design_name_rec in missions[mission_name_rec]:
                        if design_name_rec != design_name_to_remove:
                            missions_k_group[mission_name_rec].append(design_name_rec)
                        else:
                            missions_separated[mission_name_rec] = [design_name_rec]
                            

                # now running proces
                print('loading designs')
                load_designs.Load_designs(missions_k_group)
                print('identifiying framework')
                variability_framework_identifacation.identify_framework()
                print('testing framework')
                print('testing on separated design')
                test_framework(missions_separated)
                print('testing on training set')
                test_framework(missions_k_group)

                # writing test metadata file to describe what has been done
                with open('test_results/test_metadata.json', 'w') as fp:
                    json.dump({'training set':missions_k_group,'separated design':missions_separated,'tests':['compliance training','compliance separated','parameter training','parameter separated']}, fp)

                # copy over results directory to results store location
                # make folder to store results
                timestr = time.strftime("%Y%m%d-%H%M%S")
                newpath =  r'Output_store/'
                newpath = newpath + timestr
                if not os.path.exists(newpath):
                    os.makedirs(newpath)

                copy_tree("test_results", newpath+"/test_results")

def trigger_script(file_name):
    subprocess.run(["python3", file_name])

def test_framework(missions):
    # test justification for each design
    temp_name = 'temp_design'

    # load variability framework
    variability_framework = rdflib.Graph()
    variability_framework.parse("active_framework/rdf_variability_definition_1.ttl")
    mapping_module = mapping_definition_full_test_suite
    graph = Graph("bolt://localhost:7687", auth=('neo4j', 'test'))
    database_tools.clear_database(graph)

    # Add uniqueness constraints.
    database_tools.apply_constraints(graph)

    # count number of entries to be made
    process_count = 0
    for mission_name in missions.keys():
        for design_name in missions[mission_name]:
            process_count += 1

    # now load all selected designs
    process_index = 0
    with tqdm(total=process_count, colour = 'green') as pbar:
        for mission_name in missions.keys():
            for design_name in missions[mission_name]:
                # compliance testing 
                variability_framework_compliance_testing.test_compliance(mission_name,design_name,mapping_module,variability_framework,graph)

                database_tools.clear_database(graph)
                # justification testing
                test_justification_across_design(temp_name,design_name,mission_name,variability_framework,graph)
                process_index += 1
                pbar.n = process_index
                pbar.refresh()

def main():

    # test compliance
    #variability_framework_compliance_testing.test_compliance(mapping_module,variability_framework,graph)

    #####################################################################
    # Definition of Designs and requirements
    #####################################################################
    # AVDASI 2013 S1
    design_name_1 = 'AVDASI_2013_S1'

    # AVDASI 2013 S2
    design_name_2 = 'AVDASI_2013_S2'

    # AVDASI 2017 S1
    design_name_3 = 'AVDASI_2017_S1'

    # AVDASI 2017 S2
    design_name_4 = 'AVDASI_2017_S2'

    # AVDASI 2018 S1
    design_name_5 = 'AVDASI_2018_S1'

    # AVDASI 2018 S2
    design_name_6 = 'AVDASI_2018_S2'

    # AVDASI 2018 S3
    design_name_7 = 'AVDASI_2018_S3'

    # AVDASI 2020 S1
    design_name_8 = 'AVDASI_2020_S1'

    #AVDASI 2020 S2
    design_name_9 = 'AVDASI_2020_S2'

    #AVDASI 2020 S3
    design_name_10 = 'AVDASI_2020_S3'
 
    # AVDASI 2021 S1
    design_name_11 = 'AVDASI_2021_S1'

    # AVDASI 2021 S2
    design_name_12 = 'AVDASI_2021_S2'

    # AVDASI 2021 S3
    design_name_13 = 'AVDASI_2021_S3'

    #{'AVDASI_2023':['AVDASI_2023_S2']}
    #{'ESA_Proj':['ESA_Proj_Design']}

    # test all with progress bars
    #missions = {'AVDASI_2013':[design_name_1,design_name_2],'AVDASI_2017':[design_name_3,design_name_4],'AVDASI_2018':[design_name_5,design_name_6,design_name_7],'AVDASI_2020':[design_name_8,design_name_9,design_name_10],'AVDASI_2021':[design_name_11,design_name_12,design_name_13]}
    #missions = {'ESA_Proj':['ESA_Proj_Design']}
    missions = {'AVDASI_2023':['AVDASI_2023_S1','AVDASI_2023_S2','AVDASI_2023_S3']}

    #K_fold_testing(missions)
    test_framework(missions)

if __name__ == '__main__':
    main()
    