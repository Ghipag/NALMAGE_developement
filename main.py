from openai import OpenAI
import nalmage
import nalmage.ner_tools
import os
import py2neo
import rdflib
from datetime import datetime
import pyDRAGONS
from pyDRAGONS.design_editing import design_edit_tools
from pyDRAGONS.design_problem_formulation import design_problem_query_tools
from pyDRAGONS.interface import interface

def reset_transcript_file():
    log_filename = 'transcript.txt'

    now = datetime.now()
    # dd_mm_YY_H:M:S
    dt_string = now.strftime("%d_%m_%Y_%H_%M_%S")

    try:
        os.rename("transcript.txt", "transcripts/"+dt_string)
    except Exception as E:
        nalmage.ner_tools.logged_print('Error in main loop, restarting current loop')
        nalmage.ner_tools.logged_print(E)


def llm_based_design_process(design_data,design_name,mission_name,graph,variability_framework):

        
    # Use the OpenAI API key
    with open(r'c:\Users\lt17550\University of Bristol\grp-Louis-Timperley-PhD - General\Natural Language Case Study\Git_repo_Clean\api_key.txt', 'r') as fh:
        for line in fh:
            client = OpenAI(api_key = line)
            break

    # architecture navigation
    element_list = design_edit_tools.list_design_elements(design_data)
    passes_counter = 1
    
    # taking prompts as input from user and generating blocks etc. each round from completion text
    proceed_flag = True
    conversation = []
    conversation_list = []
    
    # collect what root element the user would like to start with
    nalmage.ner_tools.logged_print('***\nEnter the id of the element you wish to add to:\n***')
    i = 0
    for element in element_list:
        nalmage.ner_tools.logged_print(i)
        nalmage.ner_tools.plogged_print(element)
        i = i + 1
    nalmage.ner_tools.logged_print('\n***')
    next_element = element_list[int(nalmage.model_generation.take_text_input(''))]
    nalmage.ner_tools.logged_print(f'***\nSelected next elements is:\n {next_element}***')
    while proceed_flag:
        # firstly identify current root element
        root_element = element_list[0]
        for element in element_list:
            try:
                if element[1] == next_element[1]:
                    root_element = element
            except AttributeError as attr_error:
                nalmage.ner_tools.logged_print(attr_error)
                
        # generate reduced design rule set for current root element
        namespace = rdflib.Namespace("http://dig.isi.edu/")
        parent_reference = namespace.__getattr__(root_element[2])
        reduced_design_rules_string = nalmage.model_generation.generate_reduced_design_rule_set(parent_reference,variability_framework)

        # try:
        # select what type of model element to generate
        generate_type = nalmage.model_generation.select_element_generation_type()

        # update variables to reflect this selection i.e.: 
        # super types
        # related elements for use in prompt
        if generate_type == 'Subsystems' or generate_type == 'Components':
            super_types = ['Spacecraft','Subsystem','Unit']
            function_list = design_edit_tools.list_functions(design_data)  
            reference_type = 'functions'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in function_list:
                reference_element_string = reference_element_string + ' ' +entry

            # knowledge base query details
            query_type = 'Function to Component SA'
            grab_relationship_types = ['PARENT']
            format_string = '{[Component]:[Traceable Function]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = design_edit_tools.list_functions(design_data)
            additional_model_elements = []

        elif generate_type == 'Values':
            super_types = ['Parameter']
            requirement_text_list = design_edit_tools.list_requirements(mission_name,True,graph)
            reference_type = 'requirements'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in requirement_text_list:
                reference_element_string = reference_element_string + '\n' + entry

            # knowledge base query details
            query_type = 'Parametric Analysis'
            grab_relationship_types = ['TODO']
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = []
            additional_model_elements = []

        elif generate_type == 'loose Modes (without directly owned functions)':
            super_types = ['Mode']
            function_list = design_edit_tools.list_functions(design_data)  
            reference_type = 'functions'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in function_list:
                reference_element_string = reference_element_string + ' ' +entry

            # knowledge base query details
            query_type = 'Function to Mode SA'
            grab_relationship_types = ['PARENT']
            format_string = '{[Mode]:[Traceable Function]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = design_edit_tools.list_functions(design_data)
            additional_model_elements = []
            
        elif generate_type == 'Rigorous Modes (with owned functions)':
            super_types = ['Mode']
            function_list = design_edit_tools.list_functions(design_data)  
            reference_type = 'functions'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in function_list:
                reference_element_string = reference_element_string + ' ' +entry
            
            # knowledge base query details
            query_type = 'Function to Mode SA'
            grab_relationship_types = ['PARENT']
            format_string = '{[Mode]:[Traceable Function]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = design_edit_tools.list_functions(design_data)
            additional_model_elements = []

        elif generate_type == 'Functions':
            super_types = ['Function']
            requirement_text_list = design_edit_tools.list_requirements(mission_name,True,graph)
            reference_type = 'requirements'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in requirement_text_list:
                reference_element_string = reference_element_string + '\n' + entry

            # knowledge base query details
            query_type = 'Requirement to Function SA'
            grab_relationship_types = ['PARENT']
            format_string = '{[Function]:[Traceable Requirement]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = design_edit_tools.list_functions(design_data)
            additional_model_elements = []
        
        elif generate_type == 'SubFunctions':
            super_types = ['Function']
            function_list = design_edit_tools.list_functions(design_data)  
            reference_type = 'functions'
            # now collate these lists of reference elements into a single string for prompt
            reference_element_string = ''
            for entry in function_list:
                reference_element_string = reference_element_string + ' ' +entry
            
            # knowledge base query details
            query_type = 'Functional decomposition SA'
            grab_relationship_types = ['PARENT']
            format_string = '{[Function]:[Traceable Function]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = design_edit_tools.list_functions(design_data)
            additional_model_elements = []

        elif generate_type == 'Interfaces':  
            super_types = ['Unit']
            reference_type = 'components'
        
            # knowledge base query details
            query_type = 'Internal Interfaces Analysis' 
            grab_relationship_types = ['POWER_INTERFACE','DATA_INTERFACE','MECHANICAL_INTERFACE','FLUID_INTERFACE','THERMAL_INTERFACE']
            reference_element_string =  str(grab_relationship_types)
            format_string = '{[Target Component]:[Interface Type]}'
            requirements = design_edit_tools.list_requirements(mission_name,False,graph)
            design_variable = [root_element[1]]
            dependant_variable = []
            additional_model_elements = []
        
        # select continuing conversations
        conversation, conversation_list = nalmage.model_generation.select_conversation(conversation,conversation_list)

        # query knowledge base for expected set of elements
        design_query = {'query type':query_type,
                'requirement':requirements,
                'design variable':design_variable,
                'dependant variable':dependant_variable,
                'additional model elements':additional_model_elements}
        
        completed_query,log_record = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,design_name,graph)

        # return list of query returned type labels
        query_returned_results = []
        for grab_relationship_type in grab_relationship_types:
            if query_type == 'Internal Interfaces Analysis':
                # finding suggest dependant variable entries
                for des_var_key in completed_query['suggested dependant variable'].keys():
                    for dep_var_key in completed_query['suggested dependant variable'][des_var_key]:
                        for interface_candidate in completed_query['suggested dependant variable'][des_var_key][dep_var_key]:
                            if interface_candidate['relationship'] == grab_relationship_type:
                                query_returned_results.append(dep_var_key)
            else:
                # finding suggest children entries
                for source_type_key in completed_query['additional model elements']['children']:
                    for entry in completed_query['additional model elements']['children'][source_type_key]:
                        query_returned_results.append(entry['type'])

        nalmage.ner_tools.logged_print(query_returned_results)
        # interface.show_query_data(completed_query)

        # using language model to generate candidate elements
        selected_elements, conversation = nalmage.model_generation.prompt_llm_for_elements(True,client,conversation,generate_type,root_element,reduced_design_rules_string,reference_type,reference_element_string,query_returned_results,format_string,)

        # now generating model elements
        if generate_type == 'Subsystems' or generate_type == 'Components':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,function_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'Values':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,requirement_text_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'loose Modes (without directly owned functions)':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,function_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'Rigorous Modes (with owned functions)':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,function_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'Functions':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,requirement_text_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'SubFunctions':
            design_data,element_list = nalmage.model_generation.generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,function_list,query_returned_results,graph,variability_framework)
        elif generate_type == 'Interfaces':  
            design_data,element_list = nalmage.model_generation.generate_relationships(design_variable[0],mission_name,element_list,selected_elements,design_data,design_name,query_returned_results,graph)
        
        proceed_flag_input = nalmage.model_generation.take_text_input('***\nDo you wish to proceed?(Y/n)\n***')
        if proceed_flag_input == 'Y' or proceed_flag_input == 'y':
            proceed_flag = True
            nalmage.ner_tools.logged_print('***\nEnter the id of the element you wish to add to:\n***')
            i = 0
            for element in element_list:
                nalmage.ner_tools.logged_print(i)
                nalmage.ner_tools.plogged_print(element)
                i = i + 1
            nalmage.ner_tools.logged_print('\n***')
            next_element = element_list[int(nalmage.model_generation.take_text_input(''))]
            nalmage.ner_tools.logged_print(f'***\nSelected next elements is:\n {next_element}***')
        else:
            proceed_flag = False

        #iterate passes counter
        passes_counter = passes_counter + 1

        # except Exception as E:
        #     nalmage.ner_tools.logged_print('Error in main loop, restarting current loop')
        #     nalmage.ner_tools.logged_print(E)


def main():

    reset_transcript_file()

    # setup Neo4J database and knowledge base
    graph = py2neo.Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'test'))
    pyDRAGONS.database_interaction.database_tools.clear_database(graph)

    # load variability framework
    variability_framework = rdflib.Graph()
    variability_framework.parse("active_framework/rdf_variability_definition_1.ttl")

    # load function classifiers
    function_data = pyDRAGONS.database_interaction.data_extraction.read_data('Functions')
    pyDRAGONS.database_interaction.data_extraction.process_function_classifier_data(function_data,graph)

    # load component classifiers
    component_data = pyDRAGONS.database_interaction.data_extraction.read_data('Components')
    pyDRAGONS.database_interaction.data_extraction.process_component_classifier_data(component_data,graph)
    
    # load Condition classifiers
    condition_data = pyDRAGONS.database_interaction.data_extraction.read_data('Conditions')
    pyDRAGONS.database_interaction.data_extraction.process_condition_classifier_data(condition_data,graph)

    # load mode classifiers
    mode_data = pyDRAGONS.database_interaction.data_extraction.read_data('Modes')
    pyDRAGONS.database_interaction.data_extraction.process_mode_classifier_data(mode_data,graph)

    # load parameter classifiers
    parameter_data = pyDRAGONS.database_interaction.data_extraction.read_data('Parameters')
    pyDRAGONS.database_interaction.data_extraction.process_parameter_classifier_data(parameter_data,graph)

    # AVDASI 2020
    mission_name = 'ESA_Proj'
    pyDRAGONS.database_interaction.data_extraction.load_mission_requirements(mission_name,graph)

    # my design
    #my_design_TRUTHS_parameters'
    # MATCH(n:run_2b_Design_Instance_Element)<-[r:PARENT]-(n2:run_2b_Design_Instance_Element)
    # WHERE n2:Unit OR n2:Subsystem OR n2:Spacecraft
    # RETURN n,n2,r
    design_name = 'run_2b'
    design_data = pyDRAGONS.database_interaction.data_extraction.read_data(design_name)
    pyDRAGONS.database_interaction.data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    design_query = {'query type':'Internal Interfaces Analysis',
                    'requirement':[],
                    'design variable':['Thruster'],
                    'dependant variable':[],
                    'additional model elements':[]}
    
    
    completed_query,log_record = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,design_name,graph)

    
    interface.show_query_data(completed_query)

    llm_based_design_process(design_data,design_name,mission_name,graph,variability_framework)


if __name__ == "__main__":
    main()
