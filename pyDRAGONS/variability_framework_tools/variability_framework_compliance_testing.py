import variability_framework_tools.variability_framework_textual_core as variability_framework_textual_core
import design_problem_formulation.design_problem_query_tools as design_problem_query_tools
import database_interaction.database_tools as database_tools
import database_interaction.data_extraction as data_extraction
import pprint
import json
from tqdm import tqdm

#####################################################################
# This module provides tools for testing designs
# against a particular variability framework (or set of conditions)
# or identifying that variability framework
#####################################################################

def collect_perspective_against_framework(database_entry_type,grab_classifier,direction_flags_dict : dict,graph):
    if direction_flags_dict['single']:
        if direction_flags_dict['direction'] == "OUTGOING":
            if grab_classifier:
                query = """
                    MATCH (source:"""+database_entry_type+""")-[relationship]->(neighbour)-[:CLASSIFIER]->(classifier:Classifier)
                    RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,classifier AS neighbour,labels(classifier) AS target_labels
                """
            else:
                query = """
                            MATCH (source:"""+database_entry_type+""")-[relationship]->(neighbour)
                            RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,neighbour,labels(neighbour) AS target_labels
                            """
        if direction_flags_dict['direction'] == "INCOMING":
            if grab_classifier:
                query = """
                    MATCH (source:"""+database_entry_type+""")<-[relationship]-(neighbour)-[:CLASSIFIER]->(classifier:Classifier)
                    RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,classifier AS neighbour,labels(classifier) AS target_labels
                """
            else:
                query = """
                            MATCH (source:"""+database_entry_type+""")<-[relationship]-(neighbour)
                            RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,neighbour,labels(neighbour) AS target_labels
                            """
    else:
        if grab_classifier:
            query = """
                MATCH (source:"""+database_entry_type+""")-[relationship]-(neighbour)-[:CLASSIFIER]->(classifier:Classifier)
                RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,classifier AS neighbour,labels(classifier) AS target_labels
            """
        else:
            query = """
                        MATCH (source:"""+database_entry_type+""")-[relationship]-(neighbour)
                        RETURN source,relationship,type(relationship) AS relationship_type,startNode(relationship) AS relationship_source,neighbour,labels(neighbour) AS target_labels
                        """
    response = database_tools.run_neo_query(['nil'],query,graph)
    return response

def identify_element_type_from_mapping(node_tag,type_mapping):
    #print(f'element type tag is:{node_tag}')
    element_type = type_mapping[node_tag]
    return element_type

def identify_relationship_class_from_mapping(relationship_tag,relationship_mapping,framework_module):
    #print(f'relationship tag is:{relationship_tag}')
    relationship_class_str = relationship_mapping[relationship_tag]
    class_handle = getattr(framework_module, relationship_class_str)
    return class_handle

def test_edge_compliance_against_framework(edge,variability_framework):

    root_type = edge[0]
    relationship_type = edge[1]
    target_type = edge[2]
    result = False
    # test expected direction
    query = """
            SELECT DISTINCT ?targetclass
            WHERE {
                    :"""+root_type+""" :"""+relationship_type+""" ?targetclass  ;
    }"""
            
    outqres = variability_framework.query(query)
    
    for row in outqres:
        if design_problem_query_tools.process_uriref_string(row.targetclass) == target_type:
            result = True
            break
            
    return {'result':result,'edge':edge}

def test_perspective_against_framework(database_entry_type,relationship_edges,thing_uid_list,thing_list,database_compliance,grab_classifier,mapping_module,variability_framework,graph):
    direction_flags_dict = {}
    direction_flags_dict['single'] = True
    
    # first testing outgoing relationships
    direction_flags_dict['direction'] = 'OUTGOING'
    response = collect_perspective_against_framework(database_entry_type,grab_classifier,direction_flags_dict,graph)
    for entry in response:
        # create thing object of source if new
        if entry['source']['uid'] not in thing_uid_list:
            thing_uid_list.append(entry['source']['uid'])
            thing_list.append(variability_framework_textual_core.Thing(entry['source']['uid'],database_entry_type))
        source_index = thing_uid_list.index(entry['source']['uid'])

        # create thing object of target if new
        target_types = mapping_module.identify_target_types(entry['target_labels'])
        for target_type in target_types:
            if entry['neighbour']['uid'] not in thing_uid_list:
                thing_uid_list.append(entry['neighbour']['uid'])
                thing_list.append(variability_framework_textual_core.Thing(entry['neighbour']['uid'],target_type))

            # need to ensure source and target are right way round
            #print(f"source node is: {entry['relationship_source']['uid']}")
            edge = [database_entry_type,entry['relationship_type'],target_type]

            # test the edge: node - relationship - target node
            database_compliance.append(test_edge_compliance_against_framework(edge,variability_framework))

            relationship_edges.append(edge)


    # now testing incoming relationships
    direction_flags_dict['direction'] = 'INCOMING'
    response = collect_perspective_against_framework(database_entry_type,grab_classifier,direction_flags_dict,graph)
    for entry in response:
        # create thing object of source if new
        if entry['source']['uid'] not in thing_uid_list:
            thing_uid_list.append(entry['source']['uid'])
            thing_list.append(variability_framework_textual_core.Thing(entry['source']['uid'],database_entry_type))
        source_index = thing_uid_list.index(entry['source']['uid'])

        # create thing object of target if new
        target_types = mapping_module.identify_target_types(entry['target_labels'])
        for target_type in target_types:
            if entry['neighbour']['uid'] not in thing_uid_list:
                thing_uid_list.append(entry['neighbour']['uid'])
                thing_list.append(variability_framework_textual_core.Thing(entry['neighbour']['uid'],target_type))

            # need to ensure source and target are right way round
            #print(f"source node is: {entry['relationship_source']['uid']}")
            edge = [target_type,entry['relationship_type'],database_entry_type]

            # test the edge: node - relationship - target node
            database_compliance.append(test_edge_compliance_against_framework(edge,variability_framework))
            
            relationship_edges.append(edge) # reversed for incoming relationships

    return database_compliance,relationship_edges

def test_database_against_framework(labeled_types,thing_uid_list,thing_list,relationship_edges,database_compliance,mapping_module,variability_framework,controlled_flag,graph):
    if controlled_flag:
        # testing comparison direct neighbours    
        database_compliance,relationship_edges = test_perspective_against_framework(labeled_types[0],relationship_edges,thing_uid_list,thing_list,database_compliance,False,mapping_module,variability_framework,graph)

        # testing difference direct neighbours
        database_compliance,relationship_edges = test_perspective_against_framework(labeled_types[1],relationship_edges,thing_uid_list,thing_list,database_compliance,False,mapping_module,variability_framework,graph)

        # testing difference direct neighbours
        database_compliance,relationship_edges = test_perspective_against_framework(labeled_types[2],relationship_edges,thing_uid_list,thing_list,database_compliance,False,mapping_module,variability_framework,graph)

    else:
        for type in tqdm(labeled_types, colour ='green'):
            # exploring current type and direct neighbours
            #print(f'exploring {type} info')
            database_compliance,relationship_edges = test_perspective_against_framework(type,relationship_edges,thing_uid_list,thing_list,database_compliance,False,mapping_module,variability_framework,graph)

    return database_compliance,relationship_edges

def test_compliance(mission_name,design_name,mapping_module,variability_framework,graph):
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

    # load full design data
    design_data = data_extraction.read_data(design_name)
    data_extraction.process_design_data(mission_name,design_name,design_data,graph)

    labeled_types = mapping_module.define_labelled_types()
    
    # test the design against the framework
    design_compliance = []
    relationship_edges = []
    

    thing_uid_list = []
    thing_list = []

    # firstly considering compliance
    design_compliance,relationship_edges = test_database_against_framework(labeled_types,thing_uid_list,thing_list,relationship_edges,design_compliance,mapping_module,variability_framework,False,graph)

    # counting coverages
    compliance_count = 0
    failed_list = []
    for test_entry in design_compliance:
        if test_entry['result']:
            compliance_count += 1
        else:
            failed_list.append(test_entry['edge'])
    print(design_compliance)
    print(compliance_count)
    print(design_compliance)
    compliance = compliance_count/len(design_compliance)
    results = {'result': compliance,'failed edges':failed_list}
    #print('failed edges:')
    pprint.pprint(failed_list)
    #print(f'compliance with framework is {compliance*100}%')
    with open('test_results/'+mission_name+'_'+design_name+'_compliance_test_result.json', 'w') as fp:
        json.dump(results, fp)
