import database_interaction.data_extraction as data_extraction
import pandas as pd
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from py2neo import Graph
import pprint
import design_editing.design_edit_tools as design_edit_tools
import design_editing.requirement_parsing as requirement_parsing

graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'test'))


def main():
    #####################################################################
    # Setup and loading of database data
    # Starting with derived Ontology for AVDASI Designs
    # Then looping Design instances to update element types
    #####################################################################

    # start interface
    colorama_init()
    #interface_instance = interface.initialise_editor()
    
    # load function classifiers
    function_data = data_extraction.read_data('Functions')
    # load component classifiers
    component_data = data_extraction.read_data('Components')
    # load Condition classifiers
    condition_data = data_extraction.read_data('Conditions')
    # load mode classifiers
    mode_data = data_extraction.read_data('Modes')
    # load parameter classifiers
    parameter_data = data_extraction.read_data('Parameters')

    
    #####################################################################
    # Loop Through and Edit Designs 
    #####################################################################
    design_names = ['AVDASI_2013_S1','AVDASI_2013_S2','AVDASI_2017_S1','AVDASI_2017_S2','AVDASI_2018_S1','AVDASI_2020_S1','AVDASI_2020_S2','AVDASI_2020_S3','AVDASI_2020_S3','AVDASI_2021_S1','AVDASI_2021_S2','AVDASI_2021_S3']
    mission_names = ['AVDASI_2020']
    
    design_name_1 = 'AVDASI_2013_S1'

    # AVDASI 2013 S2
    design_name_2 = 'AVDASI_2013_S2'
    
    # AVDASI 2017

    # AVDASI 2017 S1
    design_name_3 = 'AVDASI_2017_S1'

    # AVDASI 2017 S1
    design_name_4 = 'AVDASI_2017_S2'

    # AVDASI 2018

    # AVDASI 2018 S1
    design_name_5 = 'AVDASI_2018_S1'

    # AVDASI 2018 S2
    design_name_6 = 'AVDASI_2018_S2'

    # AVDASI 2018 S2
    design_name_7 = 'AVDASI_2018_S3'

    # AVDASI 2020
    mission_name_4 = 'AVDASI_2020'

    # AVDASI 2020 S1
    design_name_8 = 'AVDASI_2020_S1'

    #AVDASI 2020 S2
    design_name_9 = 'AVDASI_2020_S2'

    #AVDASI 2020 S3
    design_name_10 = 'AVDASI_2020_S3'

    # AVDASI 2021
    mission_name_5 = 'AVDASI_2021'
 
    # AVDASI 2021 S1
    design_name_11 = 'AVDASI_2021_S1'

    # AVDASI 2021 S2
    design_name_12 = 'AVDASI_2021_S2'

    # AVDASI 2021 S3
    design_name_13 = 'AVDASI_2021_S3'
    #'AVDASI_2013':[design_name_1,design_name_2],'AVDASI_2017':[design_name_3,design_name_4],'AVDASI_2018':[design_name_5,design_name_6,design_name_7],'AVDASI_2020':[design_name_8,design_name_9,design_name_10],'AVDASI_2021':[design_name_11,design_name_12,design_name_13]
    missions = {'AVDASI_2023':['AVDASI_2023_S3']}#'AVDASI_2013':[design_name_1,design_name_2],'AVDASI_2017':[design_name_3,design_name_4],'AVDASI_2018':[design_name_5,design_name_6,design_name_7],'AVDASI_2020':[design_name_8,design_name_9,design_name_10],'AVDASI_2021':[design_name_11,design_name_12,design_name_13],'AVDASI_2023':['AVDASI_2023_S2'],'ESA_Proj':['ESA_Proj_Design']}
    design_names = list(missions.values())
    #flatten to simple list
    design_names = [    x    for xs in design_names    for x in xs    ]

    #for name in missions.keys():
    #    response = input(f'parse mission requirement? {Fore.RED}{name}{Style.RESET_ALL} (y)')
    #    if response == 'y':
    #        requirement_parsing.parse_mission_requirements(name)

    for name in missions.keys():
        #design_edit_tools.list_domain_labels(name)
        response = input(f'edit mission requirements? {Fore.RED}{name}{Style.RESET_ALL} (y)')
        if response == 'y':
           design_edit_tools.edit_mission_domains(name,graph)

    for name in design_names:
        design_edit_tools.list_sub_class_labels(name)
        response = input(f'edit design functions? {Fore.RED}{name}{Style.RESET_ALL} (y)')
        if response == 'y':
            design_edit_tools.edit_design_functions(name,missions,mode_data,component_data)

    for name in design_names:
        response = input(f'edit design subclasses? {Fore.RED}{name}{Style.RESET_ALL} (y)')
        if response == 'y':
            design_edit_tools.edit_design_subclasses(name,component_data)
    
    for name in design_names:
        response = input(f'infer functional assignments for design? {Fore.RED}{name}{Style.RESET_ALL} (y)')
        if response == 'y':
            design_edit_tools.infer_functional_assignments(name,function_data,graph)

    domain_list = []
    for name in missions.keys():
        domain_list.extend(design_edit_tools.list_domain_labels(name))

    pprint.pprint(set(domain_list))

    sub_class_list = []
    for name in design_names:
        sub_class_list.extend(design_edit_tools.list_sub_class_labels(name))

    pprint.pprint(set(sub_class_list))

    # now printing classifier types
    pprint.pprint(design_edit_tools.list_classifiers_of_type(component_data))
    pprint.pprint(design_edit_tools.list_classifiers_of_type(mode_data))
    pprint.pprint(design_edit_tools.list_classifiers_of_type(parameter_data))
    
 
if __name__ == "__main__":
    main()
