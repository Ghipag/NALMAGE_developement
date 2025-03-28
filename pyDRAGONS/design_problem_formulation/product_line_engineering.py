from pyDRAGONS.interface import interface as interface
from pyDRAGONS.design_problem_formulation import design_problem_query_tools as design_problem_query_tools
from pyDRAGONS.database_interaction import database_tools as database_tools

def check_feautre_type(feature_name,variability_framework):
    query = """
            SELECT DISTINCT ?feature_type
            WHERE {
                    :"""+feature_name+""" :FEATURE_TYPE* ?feature_type.
        }"""
            
    outqres = variability_framework.query(query)
    feature_type = 'unknown'
    for row in outqres:
        result = design_problem_query_tools.process_uriref_string(row.feature_type)
        if not result == feature_name:
            feature_type = result
    return feature_type

def list_requirement_names(graph):
    query = """
    MATCH(n:Requirement) RETURN n
    """
    response = database_tools.run_neo_query(['nil'],query,graph)
    req_names = []
    for entry in response:
        req_names.append(entry['n']['name'])
    return req_names

def list_design_element_names(design_name,graph):
    query = """
      MATCH(n:"""+design_name+"""_Design_Instance_Element) RETURN n
    """
    response = database_tools.run_neo_query(['nil'],query,graph)
    des_names = []
    for entry in response:
        des_names.append(entry['n']['name'])
    return des_names

def list_existing_features(possible_secondary_types,design_name,graph):
    query = """
            MATCH (current_element:"""+design_name+"""_Design_Instance_Element)
            Return current_element 
        """
    response = database_tools.run_neo_query(['nil'],query,graph)
    for entry in response:
        possible_secondary_types.append(entry['current_element']['name'] + ' [existing]')
    return possible_secondary_types
    

def present_product_line_info(completed_query,design_name,mission_name,graph,variability_framework):
    interface_instance = interface.initialise() 
    interface.display_product_line(interface_instance,completed_query,design_name,mission_name,graph,variability_framework)