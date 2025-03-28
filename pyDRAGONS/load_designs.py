from py2neo import Graph
import database_interaction.database_tools as database_tools
import database_interaction.data_extraction as data_extraction
import interface.interface as interface
import design_comparison.design_comparison as design_comparison
import graph_export
import design_editing.requirement_parsing as requirement_parsing
import pandas as pd
from tqdm import tqdm

def Load_designs(missions,do_comparison = True):
    database_tools.clear_database(graph)

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

    # count number of entries to be made
    process_count = 0
    for mission_name in missions.keys():
        process_count += 1
        for design_name in missions[mission_name]:
            process_count += 1

    # now load all selected designs
    process_index = 0
    mission_index = 0
    with tqdm(total=process_count, colour = 'green') as pbar1:
        with tqdm(total=len(missions.keys()), colour = 'green') as pbar2:
            for mission_name in missions.keys():
                with tqdm(total=len(missions[mission_name]), colour = 'green') as pbar3:
                    data_extraction.load_mission_requirements(mission_name,graph)
                    process_index += 1
                    mission_index += 1
                    design_index = 0
                    pbar1.n = process_index
                    pbar1.refresh()
                    pbar2.n = mission_index
                    pbar2.refresh()
                    for design_name in missions[mission_name]:
                        design_data = data_extraction.read_data(design_name)
                        data_extraction.process_design_data(mission_name,design_name,design_data,graph)
                        process_index += 1
                        design_index += 1
                        pbar1.n = process_index
                        pbar1.refresh()
                        pbar3.n = design_index
                        pbar3.refresh()

    # for error checking, return and print all nodes that have only one label (likely to be errors)
    query = """
            MATCH(s)
            WHERE SIZE(LABELS(s)) = 1
            RETURN s
        """
    response = database_tools.run_neo_query(['nil'],query,graph)

    print('displaying possible error nodes:')
    for entry in response:
        print(entry)

        # for parentless parameters
    query = "MATCH (a:Parameter) WHERE NOT (a)-[:PARENT]->() RETURN a"

    response = database_tools.run_neo_query(['nil'],query,graph)
    print('displaying parent-less parameters:')
    for entry in response:
        print(entry)
    

    #####################################################################
    # Comparison of Designs 
    #####################################################################
    # perform diff algorithm on all sets
    if do_comparison:
        design_comparison.population_wide_diff_algorithm(missions,graph)

    # create figures to present data
    # design_comparison.population_wide_generate_comparison_stats(missions,graph)

    # export some data to edge list format
    #graph_export.export_all_designs_to_edge_list(graph,missions)

    #####################################################################
    # User Interface
    #####################################################################

    # Finally generate pop up window to display diagram generation commands

#####################################################################
# Graph database config
#####################################################################

# Set up a link to the local graph database.
# Ideally get password from ENV variable
# graph = Graph(getenv("NEO4J_URL"), auth=(getenv("NEO4J_UID"), getenv("NEO4J_PASSWORD")))

graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'test'))

# Add uniqueness constraints.
database_tools.apply_constraints(graph)

def main():
  
    #####################################################################
    # Setup and loading of database data
    # Starting with derived Ontology for AVDASI Designs
    # Then Loading Design instances
    #####################################################################
    interface_instance = interface.initialise()   

    #####################################################################
    # Definition of Designs and requirements
    #####################################################################

    # AVDASI 2013
    mission_name_1 = 'AVDASI_2013'
    #data_extraction.load_mission_requirements(mission_name_1,graph)

    # AVDASI 2013 S1
    design_name_1 = 'AVDASI_2013_S1'
    #design_data = data_extraction.read_data(design_name_1)
    #data_extraction.process_design_data(mission_name_1,design_name_1,design_data,graph)

    # AVDASI 2013 S2
    design_name_2 = 'AVDASI_2013_S2'
    #design_data = data_extraction.read_data(design_name_2)
    #data_extraction.process_design_data(mission_name_1,design_name_2,design_data,graph)
    
    # AVDASI 2017
    mission_name_2 = 'AVDASI_2017'
    #data_extraction.load_mission_requirements(mission_name_2,graph)

    # AVDASI 2017 S1
    design_name_3 = 'AVDASI_2017_S1'
    #design_data = data_extraction.read_data(design_name_3)
    #data_extraction.process_design_data(mission_name_2,design_name_3,design_data,graph)

    # AVDASI 2017 S2
    design_name_4 = 'AVDASI_2017_S2'
    #design_data = data_extraction.read_data(design_name_4)
    #data_extraction.process_design_data(mission_name_2,design_name_4,design_data,graph)

    # AVDASI 2018
    mission_name_3 = 'AVDASI_2018'
    #data_extraction.load_mission_requirements(mission_name_3,graph)

    # AVDASI 2018 S1
    design_name_5 = 'AVDASI_2018_S1'
    #design_data = data_extraction.read_data(design_name_5)
    #data_extraction.process_design_data(mission_name_3,design_name_5,design_data,graph)

    # AVDASI 2018 S2
    design_name_6 = 'AVDASI_2018_S2'
    #design_data = data_extraction.read_data(design_name_6)
    #data_extraction.process_design_data(mission_name_3,design_name_6,design_data,graph)

    # AVDASI 2018 S3
    design_name_7 = 'AVDASI_2018_S3'
    #design_data = data_extraction.read_data(design_name_7)
    #data_extraction.process_design_data(mission_name_3,design_name_7,design_data,graph)

    # AVDASI 2020
    mission_name_4 = 'AVDASI_2020'
    #data_extraction.load_mission_requirements(mission_name_4,graph)

    # AVDASI 2020 S1
    design_name_8 = 'AVDASI_2020_S1'
    #design_data = data_extraction.read_data(design_name_8)
    #data_extraction.process_design_data(mission_name_4,design_name_8,design_data,graph)

    #AVDASI 2020 S2
    design_name_9 = 'AVDASI_2020_S2'
    #design_data = data_extraction.read_data(design_name_9)
    #data_extraction.process_design_data(mission_name_4,design_name_9,design_data,graph)

    #AVDASI 2020 S3
    design_name_10 = 'AVDASI_2020_S3'
    #design_data = data_extraction.read_data(design_name_10)
    #data_extraction.process_design_data(mission_name_4,design_name_10,design_data,graph)

    # AVDASI 2021
    mission_name_5 = 'AVDASI_2021'
    #data_extraction.load_mission_requirements(mission_name_5,graph)
 
    # AVDASI 2021 S1
    design_name_11 = 'AVDASI_2021_S1'
    #design_data = data_extraction.read_data(design_name_11)
    #data_extraction.process_design_data(mission_name_5,design_name_11,design_data,graph)

    # AVDASI 2021 S2
    design_name_12 = 'AVDASI_2021_S2'
    #design_data = data_extraction.read_data(design_name_12)
    #data_extraction.process_design_data(mission_name_5,design_name_12,design_data,graph)

    # AVDASI 2021 S3
    design_name_13 = 'AVDASI_2021_S3'
    #design_data = data_extraction.read_data(design_name_13)
    #data_extraction.process_design_data(mission_name_5,design_name_13,design_data,graph)

    # load all with progress bars
    #{'ESA_Proj':['ESA_Proj_Design']}
    #{'AVDASI_2023':['AVDASI_2023_S1','AVDASI_2023_S2','AVDASI_2023_S3']}
    #{'AVDASI_2013':[design_name_1,design_name_2],'AVDASI_2017':[design_name_3,design_name_4],'AVDASI_2018':[design_name_5,design_name_6,design_name_7],'AVDASI_2020':[design_name_8,design_name_9,design_name_10],'AVDASI_2021':[design_name_11,design_name_12,design_name_13],'AVDASI_2023':['AVDASI_2023_S1','AVDASI_2023_S2','AVDASI_2023_S3'],'ESA_Proj':['ESA_Proj_Design']}
    missions = {'AVDASI_2020':[design_name_8]}
    #missions = {'AVDASI_2023':['AVDASI_2023_S1','AVDASI_2023_S2','AVDASI_2023_S3']}
    #missions = {'ESA_Proj':['ESA_Proj_Design']}
    Load_designs(missions,do_comparison = False)
    
    interface.display_diagram_commands(interface_instance,missions)
 
if __name__ == "__main__":
    main()
