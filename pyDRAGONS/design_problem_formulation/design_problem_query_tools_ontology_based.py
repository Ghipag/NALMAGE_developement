import database_interaction.database_tools as database_tools
import interface.interface as interface
import database_interaction.data_extraction as data_extraction
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
import json 
import copy
import rdflib


colorama_init()

def identify_candidate_neighbours(root_type,variability_framework, include_superclass :bool):
    return identify_candidate_neighbours_class_orientated(root_type,variability_framework, include_superclass)

def identify_candidate_neighbours_class_orientated(root_type,variability_framework, include_superclass :bool):
    # finding out going relationships
    outgoing_list = []
    if include_superclass:
        # staring with (if it exists and allowed) a super class of the current class
        query = """
            SELECT DISTINCT ?property ?neighbour ?superclass
            WHERE {
                    :"""+root_type+""" a/rdfs:subClassOf* ?superclass.
                    ?superclass ?property ?neighbour .
        }"""
            
        outqres = variability_framework.query(query)
        

        first_pass = True
        for row in outqres:
            # adding immediate super class relationship (only on first pass of loop)
            if first_pass == True:    
                outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.superclass)])
                first_pass = False

            if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison'and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier':
                outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour)]) 

    query = """
        SELECT DISTINCT ?property ?property_class ?neighbour
        WHERE {
                :"""+root_type+""" ?property ?neighbour
    }"""
    outqres = variability_framework.query(query)#

    for row in outqres:
        if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison' and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier': 
            outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour)])     

    # finding incoming relationships
    query = """
    SELECT DISTINCT ?property    ?neighbour
    WHERE {
            ?neighbour ?property :"""+root_type+""" ;
    }"""

    inqres = variability_framework.query(query)
    incoming_list = []
    for row in inqres:
        if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison' and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier':
            incoming_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour)])

    return {'incoming':incoming_list,'outgoing':outgoing_list}

def identify_candidate_neighbours_relationship_orientated(root_type,variability_framework, include_superclass :bool):
    # finding out going relationships
    outgoing_list = []
    if include_superclass:
        # staring with (if it exists and allowed) a super class of the current class
        query = """
            SELECT DISTINCT ?property ?property_class ?neighbour ?superclass
            WHERE {
                    :"""+root_type+""" a/rdfs:subClassOf* ?superclass.
                    ?superclass ?property ?property_class.
                    ?property_class ?property ?neighbour .
        }"""
    
        outqres = variability_framework.query(query)

        first_pass = True
        for row in outqres:
            # adding immediate super class relationship (only on first pass of loop)
            if first_pass == True:    
                outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.superclass)])
                first_pass = False

            if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison'and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier':
                outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour)]) 

    query = """
        SELECT DISTINCT ?property ?property_class ?neighbour
        WHERE {
                :"""+root_type+""" ?property ?property_class.
                ?property_class ?property ?neighbour
    }"""
    outqres = variability_framework.query(query)#

    for row in outqres:
        if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison' and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier': 
            outgoing_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour)])     

    # finding incoming relationships
    query = """
    SELECT DISTINCT ?property ?property_class ?neighbour ?confidence_val ?support_val ?lift_val
    WHERE {
            ?property_class ?property :"""+root_type+""" ;
                    :confidence ?confidence_val ;
                    :support ?support_val ;
                    :lift ?lift_val ;
                    ?property ?neighbour
    }"""

    inqres = variability_framework.query(query)
    incoming_list = []
    for row in inqres:
        if process_uriref_string(row.neighbour) != root_type and process_uriref_string(row.neighbour) != 'Comparison' and process_uriref_string(row.neighbour) != 'Difference' and process_uriref_string(row.neighbour) != 'Classifier':
            incoming_list.append([process_uriref_string(row.property),process_uriref_string(row.neighbour),row.confidence_val.split("'")[0],row.support_val.split("'")[0],row.lift_val.split("'")[0]])

    return {'incoming':incoming_list,'outgoing':outgoing_list}

def process_uriref_string(uriref):
    if '22-rdf-syntax-ns#'in uriref:
        return uriref.split('22-rdf-syntax-ns#')[1]
    else:
        return uriref.split('/')[-1]

def check_for_relevant_type(labels,root_element_info):
    continue_flag = False
    if ('Comparison' not in labels['classifier']) and ('Difference' not in labels['classifier']) and ('Type' not in labels['classifier']) and (root_element_info['relationship_type'] != 'type'):
        continue_flag = True
    return continue_flag

def identify_super_classes(labels,variability_framework):
    # this function is at risk of entering infinite loop
    # loop super class query until no more super classes found
    element_type = labels['classifier']
    superclass_list = []
    super_class_exists = True
    while super_class_exists:
        # find super class labels
        query = """
            SELECT DISTINCT ?superclass
            WHERE {
                    :"""+str(element_type)+""" a/rdfs:subClassOf* ?superclass.
        }"""
        outqres = variability_framework.query(query)
        
        end_search = True
        for row in outqres: 
            superclass = process_uriref_string(row.superclass)

            # check if in circular loop
            if superclass not in superclass_list:
                superclass_list.append(superclass)
                end_search = False
                # update element_type search label
                element_type = superclass
            
            else:
                print(f'{Fore.YELLOW}WARNING: circular hierarchy detected, exiting superclass search loop for type {Fore.BLUE}{element_type}{Style.RESET_ALL}')
                end_search = True
        
        # break search loop if no super class found
        if end_search:
            super_class_exists = False

    return superclass_list

def identify_sub_classes(labels,subclass_list,variability_framework,debug):
    # this function is at risk of entering infinite loop
    # recursive function to query until no more sub classes found
    element_type = labels['classifier']
    # find sub class labels
    query = """
        SELECT DISTINCT ?subclass
        WHERE {
                ?subclass a/rdfs:subClassOf* :"""+element_type+""".
    }"""
    outqres = variability_framework.query(query)
    circular_detected = False
    for row in outqres: 
        subclass = process_uriref_string(row.subclass)
        if subclass not in subclass_list:
            subclass_list.append(subclass)
            # update element_type search label
            labels['classifier'] = subclass
            identify_sub_classes(labels,subclass_list,variability_framework,debug)
        else:
            circular_detected = True
            if debug == True:
                print(f'{Fore.YELLOW}WARNING: circular hierarchy detected, exiting subclass search loop for type {Fore.BLUE}{element_type}{Style.RESET_ALL}')
    
    return subclass_list, circular_detected

def identify_child_types(labels,variability_framework,debug):
    # collect super class labels
    superclass_candidate_list = identify_super_classes(labels,variability_framework)

    #only select relevant labels
    superclass_list = []
    for superclass in superclass_candidate_list:
        if check_for_relevant_type({'classifier':superclass}, {'relationship_type':''}):
            superclass_list.append(superclass)

    # collect subclass labels
    subclass_list = []
    subclass_list,circular_detected = identify_sub_classes(labels,subclass_list,variability_framework,debug)

    return superclass_list, subclass_list, circular_detected
    
def test_if_specific(test_type,variability_framework,debug):
    superclass_list, subclass_list,circular_detected = identify_child_types({'classifier':test_type},variability_framework,debug)
    if not subclass_list:
        return True, circular_detected
    else:
        return False, circular_detected

def identify_element_constraints(labels,variability_framework):
    element_type = labels['classifier']
    query = """
        SELECT DISTINCT ?constraint
        WHERE {
                :"""+element_type+""" :has_constraint ?constraint .
    }"""
    qres = variability_framework.query(query)
    constraint_list = []
    for row in qres:
        constraint_list.append( process_uriref_string(row.constraint))

    return constraint_list
     
def categorize_neighbours(neighbours):
    interfaces = []
    dependencies = []
    influenced_elements = []
    Requirement_Domains = []
    satisfying_components = []
    parents = []
    children = []
    comparisons = []
    active_components = []
    related_modes = []
    assigned_functions = []
    assigned_to_components = []
    grouped_functions = []
    grouped_to_modes = []
    # loop through all neighbours
    for key in neighbours.keys():
        for neighbour in neighbours[key]:
            if 'INTERFACE' in neighbour[0]:
                interfaces.append(neighbour)
            elif 'DEPENDENCY' in neighbour[0]:
                if key == 'incoming':
                    influenced_elements.append(neighbour)
                elif key == 'outgoing':
                    dependencies.append(neighbour)
            elif 'SATISFY' in neighbour[0]:
                if '_Domain' in neighbour[1]:
                    satisfying_components.append(neighbour)
                else:
                    Requirement_Domains.append(neighbour)
            elif 'PARENT' in neighbour[0]:
                if key == 'incoming':
                    children.append(neighbour)
                elif key == 'outgoing':
                    parents.append(neighbour)
            elif 'COMPARISON' in neighbour[0] or 'DIFFERENCE' in neighbour[0]:
                comparisons.append(neighbour)
            elif 'ACTIVE' in neighbour[0]:
                if key == 'incoming':
                    related_modes.append(neighbour)
                elif key == 'outgoing':
                    active_components.append(neighbour)
            elif 'ASSIGNED_TO' in neighbour[0]:
                if key == 'incoming':
                    assigned_functions.append(neighbour)
                elif key == 'outgoing':
                    assigned_to_components.append(neighbour)
            elif 'GROUPED_TO' in neighbour[0]:
                if key == 'incoming':
                    grouped_functions.append(neighbour)
                elif key == 'outgoing':
                    grouped_to_modes.append(neighbour)
    return {'interfaces':interfaces,'dependencies':dependencies,'influenced elements':influenced_elements,'requirement domains':Requirement_Domains,
                    'satisfying elements': satisfying_components,'parents':parents,'children':children,'comparisons':comparisons,'active components':active_components,
                    'related modes':related_modes,'assigned functions':assigned_functions,'assigned to components':assigned_to_components,'grouped_functions':grouped_functions,
                    'grouped_to_modes':grouped_to_modes}

def filter_for_specific_types(candidate_neighbours,variability_framework):
    neighbours = {'incoming':[],'outgoing':[]}
    for key in candidate_neighbours.keys():
        for element_type in candidate_neighbours[key]:
            labels = {'classifier':element_type[1],'multiplicity':1,'superclasses': []}
            
            # check sub and super classes
            superclass_list, subclass_list,circular_detected = identify_child_types(labels,variability_framework,True)
            if not subclass_list:
                neighbours[key].append(element_type)
    return neighbours

def localise_context_to_design(catergorised_neighbours,root_local_element_uid,graph):
    non_localise_types = ['comparisons']
    neighbours = {}
    for key in catergorised_neighbours.keys():
        abstract_neighbours_in_category = catergorised_neighbours[key]
        if key not in non_localise_types:
            neighbours[key] = {}        

            # loop through current abstract neighbour types and query design graph for localised neighbours
            for abstract_neighbour in abstract_neighbours_in_category:
                neighbours[key][abstract_neighbour[0]+'/'+abstract_neighbour[1]] = {}
                # add entry for abstract
                neighbours[key][abstract_neighbour[0]+'/'+abstract_neighbour[1]]['abstract'] = abstract_neighbour

                # initialse local list
                neighbours[key][abstract_neighbour[0]+'/'+abstract_neighbour[1]]['local'] = []

                # query for local
                query = """
                    MATCH (root_local_element {uid:'"""+root_local_element_uid+"""'})-[r:"""+abstract_neighbour[0]+"""]-(local_neighbour:"""+abstract_neighbour[1]+""")
                    Return local_neighbour 
                """
                response = database_tools.run_neo_query(['nil'],query,graph)
                # check if any local elements have been returned
                if response:
                    local_neighbour = [abstract_neighbour[0],response[0]['local_neighbour']['uid']]
                    neighbours[key][abstract_neighbour[0]+'/'+abstract_neighbour[1]]['local'] = local_neighbour
    
    return neighbours

def design_context_framework_query(variability_framework,root_type,root_local_element_uid,filter_for_specific,graph):
    # identify abstract neighbour types
    candidate_neighbours = identify_candidate_neighbours(root_type,variability_framework,False)

    # remove references to non specific types if necessary
    if filter_for_specific:
        neighbours = filter_for_specific_types(candidate_neighbours,variability_framework)
    else:
        neighbours = candidate_neighbours
    

    # catergorize abstract neighbours
    catergorised_neighbours = categorize_neighbours(neighbours)

    # link (localise) to current design elements
    abstract_and_local_neighbours = localise_context_to_design(catergorised_neighbours,root_local_element_uid,graph)

    # display and return
    if any(abstract_and_local_neighbours.values()):
        pass
        #print(f'determined design context for: {Fore.GREEN}{root_type}{Style.RESET_ALL}')
        #pprint.pprint(abstract_and_local_neighbours)

    return abstract_and_local_neighbours

def key_search(search_key,current_dict,location_key_set,discovered_element_list):
    # initial values for case where no keys in current dict
    dict_entry = current_dict

    # in case where current location is actually a list (i.e. at the base level of the dict)
    # need to skip this case
    if isinstance(current_dict, dict):
        for key in current_dict.keys():
            dict_entry = current_dict[key]
            location_key_set_update = location_key_set + [key]
            if key != search_key:
                dict_entry, discovered_element_list = key_search(search_key,dict_entry,location_key_set_update,discovered_element_list)
            else:
                discovered_element_list.append([dict_entry,location_key_set_update])
    return dict_entry, discovered_element_list

def per_context_additional_type_key_search(search_key,context_element,context_element_name,suggested_additional_model_elements):
    # check if search key exists
    if search_key in context_element.keys():
        for candidate_discovered_element_key in context_element[search_key].keys():
            candidate_discovered_element = context_element[search_key][candidate_discovered_element_key]
            if not candidate_discovered_element['local']:
                suggested_additional_model_element = {'additional element':candidate_discovered_element['abstract']}
                suggested_additional_model_elements[context_element_name].append(suggested_additional_model_element)
    
    return suggested_additional_model_elements

def design_context_key_search(search_key,context,variability_framework):
    # specifically search each "top level" entry in the design context
    suggested_additional_model_elements = {}

    # requirement search
    for requiremnt_keys in context['requirement']:
        requirement = context['requirement'][requiremnt_keys]
        for domain_key in requirement.keys():
            domain = requirement[domain_key]
            suggested_additional_model_elements[domain_key] = []
            suggested_additional_model_elements = per_context_additional_type_key_search(search_key,domain,domain_key,suggested_additional_model_elements)
    print('requirement search complete')

    # design variable search (only specific types)
    for design_variable_keys in context['design variable']:
        design_variable = context['design variable'][design_variable_keys]
        for abstract_type_key in design_variable.keys():
            abstract_type = design_variable[abstract_type_key]
            labels = {'classifier':abstract_type_key,'multiplicity':1,'superclasses': []}
            # check sub and super classes
            superclass_list, subclass_list,circular_detected = identify_child_types(labels,variability_framework,True)
            # only select specific types
            if not subclass_list:
                suggested_additional_model_elements[abstract_type_key] = []
                suggested_additional_model_elements = per_context_additional_type_key_search(search_key,abstract_type,abstract_type_key,suggested_additional_model_elements)
    print('design variable search complete')

    # dependant variable search (only specific types)
    for dependant_variable_keys in context['dependant variable']:
        dependant_variable = context['dependant variable'][dependant_variable_keys]
        for abstract_type_key in dependant_variable.keys():
            abstract_type = dependant_variable[abstract_type_key]
            labels = {'classifier':abstract_type_key,'multiplicity':1,'superclasses': []}
            # check sub and super classes
            superclass_list, subclass_list, circular_detected = identify_child_types(labels,variability_framework,True)
            # only select specific types
            if not subclass_list:
                suggested_additional_model_elements[abstract_type_key] = []
                suggested_additional_model_elements = per_context_additional_type_key_search(search_key,abstract_type,abstract_type_key,suggested_additional_model_elements)
    print('dependant variable search complete')

    return suggested_additional_model_elements

def requirement_context_query(design_query,mission_name,variability_framework,graph):
    requirement_context = {}
    # firstly retrieve information about queried requirements
    for requirement in design_query['requirement']:
        requirement_context[requirement] = {}
        # getting generic types described in variability framework
        root_local_element_uid = mission_name + requirement
        query = """
                        MATCH (requirement:"""+mission_name+"""_Requirement_Element:Requirement {uid: '""" + root_local_element_uid+"""'}) 
                        RETURN labels(requirement) as labels
                        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        candidate_requirement_domains = response[0]['labels']
        requirement_domains = []
        for candidate in candidate_requirement_domains:
            if 'Domain' in candidate:
                requirement_domains.append(candidate)
        for requirement_domain in requirement_domains:
            current_context = design_context_framework_query(variability_framework,requirement_domain,root_local_element_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                requirement_context[requirement][requirement_domain] = current_context
    return requirement_context

def design_variable_context_query(design_query,design_name,variability_framework,graph):
    design_variable_context = direct_variable_design_context_query('design variable',design_query,design_name,variability_framework,graph)
    
    return design_variable_context

def dependant_variable_context_query(design_query,design_name,variability_framework,graph):
    dependant_variable_context = direct_variable_design_context_query('dependant variable',design_query,design_name,variability_framework,graph)

    return dependant_variable_context

def direct_variable_design_context_query(variable_type,design_query,design_name,variability_framework,graph):
    variable_context = {}
    # firstly retrieve information about queried variables
    for variable in design_query[variable_type]:
        variable_context[variable] = {}
        # getting generic types described in variability framework
        root_local_element_uid = design_name + variable

        query = """
                MATCH (design_Element:"""+design_name+"""_Design_Instance_Element:Design_Element {uid: '""" + root_local_element_uid+"""'}) 
                RETURN labels(design_Element) as labels
        """

        response = database_tools.run_neo_query(['nil'],query,graph)
        dependant_variable_types = response[0]['labels']

        for dependant_variable_type    in dependant_variable_types:
            current_context = design_context_framework_query(variability_framework,dependant_variable_type,root_local_element_uid,False,graph)
            # add if non empty
            if any(current_context.values()):
                variable_context[variable][dependant_variable_type] = current_context

    return variable_context
    
def suggested_dependant_variables(design_variable_context,requirement_context,design_name,mission_name,variability_framework,graph):
    suggested_dependant_variable_context    = {}
    
    # identify dependent variables as related to design variables via interface relationships, not already interfaced to in design
    for design_variable_key in design_variable_context.keys():
        suggested_dependant_variable_context[design_variable_key] = {}
        design_variable = design_variable_context[design_variable_key]
        for design_variable_type in design_variable.keys():
            # only select specific types
            if test_if_specific(design_variable_type,variability_framework,True)[0]:
                # now find interfaced elements (if any)
                for entry_key in design_variable[design_variable_type]['interfaces'].keys():
                    # access and local abstract interfaced elements
                    # need to find the abstract types that exist in the design already, 
                    # but are not currently interfaced to (i.e. no local instance currently identified)
                    dependant_variable = design_variable[design_variable_type]['interfaces'][entry_key]['local']
                    dependant_variable_abstract = design_variable[design_variable_type]['interfaces'][entry_key]['abstract']
                    # only search if not already localized and is specific type
                    if not dependant_variable and test_if_specific(dependant_variable_abstract[1],variability_framework,True)[0]:
                        # now search for instances of this abstract type in the design
                        query = """
                            MATCH (candidate_neighbour:"""+dependant_variable_abstract[1]+""":"""+design_name+"""_Design_Instance_Element)
                            Return candidate_neighbour 
                        """
                        response = database_tools.run_neo_query(['nil'],query,graph)
                        for entry in response:
                            candidate_neighbour = entry['candidate_neighbour']['name']
                            # add dependent variable contexts to dependant context dict
                            #neighbour_uid = design_name + candidate_neighbour
                            current_context = {'type':dependant_variable_abstract[1],'relationship':entry_key.split('/')[0],'traceable to':[design_variable_key,design_variable_type]}
                            if not candidate_neighbour in suggested_dependant_variable_context[design_variable_key].keys():
                                suggested_dependant_variable_context[design_variable_key][candidate_neighbour] = []
                            suggested_dependant_variable_context[design_variable_key][candidate_neighbour].append(current_context)
                            # TODO this over writes the entry if multiple interface types are allowed
                
    # identify dependent variables as related to design variables via hard dependency relationships
    for design_variable_key in design_variable_context.keys():
        design_variable = design_variable_context[design_variable_key]
        for design_variable_type in design_variable.keys():
            labels = {'classifier':design_variable_type,'multiplicity':1,'superclasses': []}
            # check sub and super classes
            superclass_list, subclass_list, circular_detected = identify_child_types(labels,variability_framework,True)
            # only select specific types
            if not subclass_list:
                # now find influenced elements (if any)
                for entry_key in design_variable[design_variable_type]['influenced elements'].keys():
                    #print(entry_key)
                    # access local influenced elements
                    dependant_variable = design_variable[design_variable_type]['influenced elements'][entry_key]['local']
                    dependant_variable_abstract = design_variable[design_variable_type]['influenced elements'][entry_key]['abstract']
                    #print(dependant_variable,dependant_variable_abstract)
                    if dependant_variable:
                        # add dependent variable contexts to dependant context dict
                        current_context = design_context_framework_query(variability_framework,dependant_variable_abstract[1],dependant_variable[1],True,graph)
                        if not dependant_variable[1] in suggested_dependant_variable_context[design_variable_key].keys():
                            suggested_dependant_variable_context[design_variable_key][dependant_variable[1]] = []
                        suggested_dependant_variable_context[design_variable_key][dependant_variable[1]].append(current_context)
    
    # now identify dependent variables as related to requirements via satisfy relationships
    for requirement_key in requirement_context.keys():
        suggested_dependant_variable_context[requirement_key] = {}
        requirement =    requirement_context[requirement_key]
        requirement_uid = mission_name + requirement_key
        relationship = 'SATISFY'
        # need to first identify requirement signals for each requirement
        query = """
                    MATCH (requirement:Requirement {uid: '""" + requirement_uid+"""'})-[r:"""+relationship+"""]-(design_element:Design_Element)
                    RETURN design_element,labels(design_element) as labels
        """

        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            design_element_uid = entry['design_element']['uid']
            
            requirement_context[requirement_key][design_element_uid] = {}
            # getting generic types described in variability framework for each design_element
            design_element_types = entry['labels']
            
            for design_element_type in design_element_types:
                current_context = design_context_framework_query(variability_framework,design_element_type,design_element_uid,True,graph)
                # add if non empty
                if any(current_context.values()):
                    if not design_element_uid in suggested_dependant_variable_context[requirement_key].keys():
                        suggested_dependant_variable_context[requirement_key][design_element_uid] = current_context

    return suggested_dependant_variable_context

def suggest_design_variables(design_variable_context,suggested_dependant_variable_context,requirement_context,design_name,mission_name,variability_framework,graph):
    # suggest design variables as a selection of the dependant variables that do not have any dependencies
    suggested_design_variable_context = {}
    for source_key  in suggested_dependant_variable_context.keys():
        for suggested_dep_var_key in suggested_dependant_variable_context[source_key].keys():
            # first corrrect entry type exists - should be dict, not list for parametric study
            if not isinstance(suggested_dependant_variable_context[source_key][suggested_dep_var_key], list):
                # if no dependencies then convert to suggested design variable
                if not suggested_dependant_variable_context[source_key][suggested_dep_var_key]['dependencies']:
                    suggested_design_variable_context[source_key] = {}
                    suggested_design_variable_context[source_key][suggested_dep_var_key] = copy.deepcopy(suggested_dependant_variable_context[source_key][suggested_dep_var_key])
    # now removing from suggested dependant variable list
    for source_key  in suggested_design_variable_context.keys():
        for suggested_des_var_key in suggested_design_variable_context[source_key].keys():  
            # TODO should probably delete the original, however it is easier to test when leaving it
            pass#del suggested_dependant_variable_context[source_key][suggested_des_var_key]
    
    return suggested_dependant_variable_context

def suggest_requirements(design_variable_context,dependant_variable_context,design_name,variability_framework,graph):    
    suggested_requirement_context    = {}
    for design_variable_key in design_variable_context.keys():
        suggested_requirement_context[design_variable_key] = {}
        design_variable = design_variable_context[design_variable_key]
        design_element_uid = design_name + design_variable_key
        # directly from design model
        query = """
                    MATCH (requirement:Requirement)-[r:PARENT_REQUIREMENT]-(requirement_clause:Requirement_Clause)-[r2:SATISFY]-(requirement_signal:Requirement_Signal)-[r3:SATISFY]-(design_element:Design_Element {uid: '""" + design_element_uid+"""'})
                    RETURN requirement
        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            requirement_uid = entry['requirement']['uid']
            current_context = design_context_framework_query(variability_framework,'Requirement',requirement_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                suggested_requirement_context[design_variable_key][requirement_uid] = current_context

    # identify requirements related to all current dependant variables as according to current design model
    for dependant_variable_key in dependant_variable_context.keys():
        suggested_requirement_context[dependant_variable_key] = {}
        dependant_variable = dependant_variable_context[dependant_variable_key]
        dependant_element_uid = design_name + dependant_variable_key
        # directly from design model
        query = """
                    MATCH (requirement:Requirement)-[r:PARENT_REQUIREMENT]-(requirement_clause:Requirement_Clause)-[r2:SATISFY]-(requirement_signal:Requirement_Signal)-[r3:SATISFY]-(design_element:Design_Element {uid: '""" + dependant_element_uid+"""'})
                    RETURN requirement
        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            requirement_uid = entry['requirement']['uid']
            current_context = design_context_framework_query(variability_framework,'Requirement',requirement_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                suggested_requirement_context[dependant_variable_key][requirement_uid] = current_context

    return suggested_requirement_context

def suggest_additional_design_model_elements(semi_completed_query,variability_framework):
    suggested_additional_model_elements= {}
    # children first
    search_key = 'children'
    suggested_additional_model_elements[search_key] = design_context_key_search(search_key,semi_completed_query,variability_framework)

    # now dependencies
    search_key = 'dependencies'
    suggested_additional_model_elements[search_key] = design_context_key_search(search_key,semi_completed_query,variability_framework)

    requirement_context = semi_completed_query['requirement']
    suggested_requirement_context = semi_completed_query['suggested requirement context']
    design_variable_context = semi_completed_query['design variable']
    dependant_variable_context = semi_completed_query['dependant variable']
    suggested_dependant_variable_context = semi_completed_query['suggested dependant variable']
    suggested_design_variable_context = semi_completed_query['suggested design variable']

    completed_query = {'query type': semi_completed_query['query type'],'requirement':requirement_context,'suggested requirement context':suggested_requirement_context,'design variable':design_variable_context,'dependant variable':dependant_variable_context,'suggested dependant variable':suggested_dependant_variable_context,'suggested design variable':suggested_design_variable_context,'additional model elements':suggested_additional_model_elements}
    
    return completed_query

def filter_additional_types(filtered_completed_query,select_types,section_key,variability_framework):
    query_result = filtered_completed_query['additional model elements'][section_key]
    # filter for allowed types
    for child_of_type in query_result.keys():
        # make list of additional selected types (empty for now)
        selected_additional_types = []
        for index in range(len(query_result[child_of_type])):
            entry = query_result[child_of_type][index]
            candidate_relationship_type = entry['additional element']

            # now loop through type class and superclasses and accept if one of these is allowed
            classes = identify_super_classes({'classifier':candidate_relationship_type[1]},variability_framework)
            classes.append(candidate_relationship_type[1])

            # select if intersection between list of current classes and allowed classes exist
            if list(set(classes).intersection(select_types)):
                selected_additional_types.append({'additional element':candidate_relationship_type})

        # now reassign selected list instead of old
        filtered_completed_query['additional model elements'][section_key][child_of_type] = selected_additional_types

    return filtered_completed_query

def select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework):
    # now further filtering for types relevant to current requirements/dependant variables
    selected_additional_types = {}
    selected_additional_types_list = []
    
    # only select types that satisfy all rules for every related type
    for type_key in filtered_completed_query['additional model elements']['children'].keys():
        selected_additional_types[type_key] = []
        for additional_element in filtered_completed_query['additional model elements']['children'][type_key]:

            for dep_key in filtered_completed_query['dependant variable'].keys():
                allowable_types_list = []
                for dep_type_key in filtered_completed_query['dependant variable'][dep_key].keys():
                    allowable_types_set = set()
                    for related_element_type_key in filtered_completed_query['dependant variable'][dep_key][dep_type_key][relevant_relationship_key]:
                        related_element_type = filtered_completed_query['dependant variable'][dep_key][dep_type_key][relevant_relationship_key][related_element_type_key]
                        # only select specific types TODO: this could cause issues with the req-to func stage
                        is_specific,circular_detected = test_if_specific(related_element_type['abstract'][1],variability_framework,True)
                        if is_specific:
                            allowable_types_set.add(related_element_type['abstract'][1])
                    allowable_types_list.append(allowable_types_set)
                # find common allowable types for all entries
                intersected_set = set.intersection(*allowable_types_list)
                intersected_list = list(intersected_set)
                if additional_element['additional element'][1] in intersected_list and not additional_element['additional element'][1] in selected_additional_types_list:
                    selected_additional_types[type_key].append({'type':additional_element['additional element'][1],'relationship':additional_element['additional element'][0],'traceable to':dep_key})
                    selected_additional_types_list.append(additional_element['additional element'][1])


    # now reassign selected list instead of old
    filtered_completed_query['additional model elements']['children'] = selected_additional_types

    return filtered_completed_query

def design_context_query(variability_framework,design_query:dict,mission_name,design_name,graph):
    # query framework about requirements
    requirement_context = requirement_context_query(design_query,mission_name,variability_framework,graph)
    
    # query framework about possible design variables (design elements to be varied)
    design_variable_context = design_variable_context_query(design_query,design_name,variability_framework,graph)

    # identify dependant variables, that exist in design
    dependant_variable_context = dependant_variable_context_query(design_query,design_name,variability_framework,graph)
    
    # now identify dependant variables as dependencies or influenced elements of the selected design variables (only specific types however)
    suggested_dependant_variable_context = suggested_dependant_variables(design_variable_context,requirement_context,design_name,mission_name,variability_framework,graph)

    # now identify suggested design variables as suggest dependent variables that have no dependencies
    suggested_design_variable_context = suggest_design_variables(design_variable_context,suggested_dependant_variable_context,requirement_context,design_name,mission_name,variability_framework,graph)

    # identify requirements related to all current design variables as according to current design model
    suggested_requirement_context  = suggest_requirements(design_variable_context,dependant_variable_context,design_name,variability_framework,graph)

    semi_completed_query = {'query type': design_query['query type'],'requirement':requirement_context,'suggested requirement context':suggested_requirement_context,'design variable':design_variable_context,'dependant variable':dependant_variable_context,'suggested dependant variable':suggested_dependant_variable_context,'suggested design variable':suggested_design_variable_context}
    
    # relevant types that do not exist in current design model
    # this is identified by looking at only specific, local design elements, identified as design variables or dependant variables
    # and selecting their abstract dependencies and children that do no exist in the model 
    completed_query = suggest_additional_design_model_elements(semi_completed_query,variability_framework)
    
    # need deep copy of query dictionary
    filtered_completed_query = copy.deepcopy(completed_query)

    # now need to filter according to current query type
    match design_query['query type']:
        case 'Requirement to Function SA':
            print('r->rd->fd')
            select_types = ['Function']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)
            
            # now further filtering for types relevant to current requirements
            selected_additional_types = {}
            # in this case function fdomains are implicitly related to requirement domains of the same name TODO come up with a formal relationship here
            for type_key in filtered_completed_query['additional model elements']['children'].keys():
                selected_additional_types[type_key] = []

                for additional_element in filtered_completed_query['additional model elements']['children'][type_key]:
                    # identify related requirement if any
                    for req_key in filtered_completed_query['requirement'].keys():
                        for req_type in filtered_completed_query['requirement'][req_key]:
                            if additional_element['additional element'][1].replace('_FDomain','') == req_type.replace('_Domain',''):
                                #print({'type':additional_element['additional element'][1],'relationship':additional_element['additional element'][0],'traceable to':req_key})
                                selected_additional_types[type_key].append({'type':additional_element['additional element'][1],'relationship':additional_element['additional element'][0],'traceable to':req_key})

            # now reassign selected list instead of old
            filtered_completed_query['additional model elements']['children'] = selected_additional_types

        case 'Function to Component SA':
            print('f->fd->cc')
            select_types = ['Subsystem','Unit']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'assigned to components'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework) 
        
        case 'Function to Mode SA':
            print('f->fd->mc')
            select_types = ['Mode']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'grouped_to_modes'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework) 
        
        case 'Functional decomposition SA':
            print('TODO')
            print('f->fd->f')
            select_types = ['FDomain']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'TODO'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)
        
        case 'Internal Interfaces Analysis':
            print('c->cc->cc->c')
            select_types = ['Unit','Subsystem','Spacecraft']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'interfaces'
            #filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)

        case 'Parametric Analysis':
            print('p->pc->pc->p')
            select_types = ['Parameter']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'dependencies',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            #relevant_relationship_key = 'grouped_to_modes'
            #filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)

    # Convert and write JSON object to file
    with open("query_result.json", "w") as outfile: 
        json.dump(filtered_completed_query, outfile)

    filtered_completed_query['query type']=filtered_completed_query['query type'].replace(' ','_')

    return filtered_completed_query

def categorize_neighbours_ontology_based(neighbours,query_ontology):
    # get neightbour relationship roles
    query = """
            SELECT DISTINCT ?context_role ?context_role_label
            WHERE {
                    ?context_role a/rdfs:subClassOf* :Role.
                    ?context_role :LABEL ?context_role_label .
        }"""

    outqres = query_ontology.query(query)
    roles_dict = {}
    for row in outqres:
        roles_dict[process_uriref_string(row.context_role_label)] = []

    # now catergorise neighbours by role
    for key in neighbours.keys():
        for neighbour in neighbours[key]:
            # query ontology for correct catergory
            query = """
                    SELECT DISTINCT ?neighbour_role ?context_role ?context_role_label
                    WHERE {
                            ?neighbour_role a/rdfs:subClassOf* :Neighbour_relationship.
                            ?neighbour_role :RELATIONSHIP '"""+neighbour[0]+"""'.
                            ?neighbour_role :DIRECTION '"""+key+"""'.
                            ?neighbour_role :RANGE ?context_role .
                            ?context_role :LABEL ?context_role_label .

                }"""
            outqres = query_ontology.query(query)
            for row in outqres:
                # catch for requirement satisfaction case 
                if 'SATISFY' in neighbour[0]:
                    if '_Domain' in neighbour[1]:
                        roles_dict['satisfying components'].append(neighbour)
                    else:
                       roles_dict['requirement domains'].append(neighbour)
                else:
                    roles_dict[process_uriref_string(row.context_role_label)].append(neighbour)
    return roles_dict

def design_context_framework_query_ontology_based(variability_framework,query_ontology,root_type,root_local_element_uid,filter_for_specific,graph):
    # identify abstract neighbour types
    candidate_neighbours = identify_candidate_neighbours(root_type,variability_framework,False)

    # remove references to non specific types if necessary
    if filter_for_specific:
        neighbours = filter_for_specific_types(candidate_neighbours,variability_framework)
    else:
        neighbours = candidate_neighbours
    

    # catergorize abstract neighbours
    catergorised_neighbours = categorize_neighbours_ontology_based(neighbours,query_ontology)

    # link (localise) to current design elements
    abstract_and_local_neighbours = localise_context_to_design(catergorised_neighbours,root_local_element_uid,graph)

    return abstract_and_local_neighbours

def requirement_context_query_ontology_based(design_query,query_ontology,mission_name,variability_framework,graph):
    requirement_context = {}
    # firstly retrieve information about queried requirements
    for requirement in design_query['requirement']:
        requirement_context[requirement] = {}
        # getting generic types described in variability framework
        root_local_element_uid = mission_name + requirement
        query = """
                        MATCH (requirement:"""+mission_name+"""_Requirement_Element:Requirement {uid: '""" + root_local_element_uid+"""'}) 
                        RETURN labels(requirement) as labels
                        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        candidate_requirement_domains = response[0]['labels']
        requirement_domains = []
        for candidate in candidate_requirement_domains:
            if 'Domain' in candidate:
                requirement_domains.append(candidate)
        for requirement_domain in requirement_domains:
            current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,requirement_domain,root_local_element_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                requirement_context[requirement][requirement_domain] = current_context
    return requirement_context

def design_variable_context_query_ontology_based(design_query,design_name,variability_framework,query_ontology,graph):
    design_variable_context = direct_variable_design_context_query_ontology_based('design variable',design_query,design_name,variability_framework,query_ontology,graph)
    
    return design_variable_context

def dependant_variable_context_query_ontology_based(design_query,design_name,variability_framework,query_ontology,graph):
    dependant_variable_context = direct_variable_design_context_query_ontology_based('dependant variable',design_query,design_name,variability_framework,query_ontology,graph)

    return dependant_variable_context

def direct_variable_design_context_query_ontology_based(variable_type,design_query,design_name,variability_framework,query_ontology,graph):
    variable_context = {}
    # firstly retrieve information about queried variables
    for variable in design_query[variable_type]:
        variable_context[variable] = {}
        # getting generic types described in variability framework
        root_local_element_uid = design_name + variable

        query = """
                MATCH (design_Element:"""+design_name+"""_Design_Instance_Element:Design_Element {uid: '""" + root_local_element_uid+"""'}) 
                RETURN labels(design_Element) as labels
        """

        response = database_tools.run_neo_query(['nil'],query,graph)
        dependant_variable_types = response[0]['labels']

        for dependant_variable_type    in dependant_variable_types:
            current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,dependant_variable_type,root_local_element_uid,False,graph)
            # add if non empty
            if any(current_context.values()):
                variable_context[variable][dependant_variable_type] = current_context

    return variable_context

def suggested_dependant_variables_ontology_based(design_variable_context,requirement_context,design_name,mission_name,variability_framework,query_ontology,graph):
    suggested_dependant_variable_context    = {}
    
    # identify dependent variables as related to design variables via interface relationships, not already interfaced to in design
    for design_variable_key in design_variable_context.keys():
        suggested_dependant_variable_context[design_variable_key] = {}
        design_variable = design_variable_context[design_variable_key]
        for design_variable_type in design_variable.keys():
            # only select specific types
            if test_if_specific(design_variable_type,variability_framework,True)[0]:
                # now find interfaced elements (if any)
                for entry_key in design_variable[design_variable_type]['interfaces'].keys():
                    # access and local abstract interfaced elements
                    # need to find the abstract types that exist in the design already, 
                    # but are not currently interfaced to (i.e. no local instance currently identified)
                    dependant_variable = design_variable[design_variable_type]['interfaces'][entry_key]['local']
                    dependant_variable_abstract = design_variable[design_variable_type]['interfaces'][entry_key]['abstract']
                    # only search if not already localized and is specific type
                    if not dependant_variable and test_if_specific(dependant_variable_abstract[1],variability_framework,True)[0]:
                        # now search for instances of this abstract type in the design
                        query = """
                            MATCH (candidate_neighbour:"""+dependant_variable_abstract[1]+""":"""+design_name+"""_Design_Instance_Element)
                            Return candidate_neighbour 
                        """
                        response = database_tools.run_neo_query(['nil'],query,graph)
                        for entry in response:
                            candidate_neighbour = entry['candidate_neighbour']['name']
                            # add dependent variable contexts to dependant context dict
                            #neighbour_uid = design_name + candidate_neighbour
                            current_context = {'type':dependant_variable_abstract[1],'relationship':entry_key.split('/')[0],'traceable to':[design_variable_key,design_variable_type]}
                            if not candidate_neighbour in suggested_dependant_variable_context[design_variable_key].keys():
                                suggested_dependant_variable_context[design_variable_key][candidate_neighbour] = []
                            suggested_dependant_variable_context[design_variable_key][candidate_neighbour].append(current_context)
                            # TODO this over writes the entry if multiple interface types are allowed
                
    # identify dependent variables as related to design variables via hard dependency relationships
    for design_variable_key in design_variable_context.keys():
        design_variable = design_variable_context[design_variable_key]
        for design_variable_type in design_variable.keys():
            labels = {'classifier':design_variable_type,'multiplicity':1,'superclasses': []}
            # check sub and super classes
            superclass_list, subclass_list, circular_detected = identify_child_types(labels,variability_framework,True)
            # only select specific types
            if not subclass_list:
                # now find influenced elements (if any)
                for entry_key in design_variable[design_variable_type]['influenced elements'].keys():
                    #print(entry_key)
                    # access local influenced elements
                    dependant_variable = design_variable[design_variable_type]['influenced elements'][entry_key]['local']
                    dependant_variable_abstract = design_variable[design_variable_type]['influenced elements'][entry_key]['abstract']
                    #print(dependant_variable,dependant_variable_abstract)
                    if dependant_variable:
                        # add dependent variable contexts to dependant context dict
                        current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,dependant_variable_abstract[1],dependant_variable[1],True,graph)
                        if not dependant_variable[1] in suggested_dependant_variable_context[design_variable_key].keys():
                            suggested_dependant_variable_context[design_variable_key][dependant_variable[1]] = []
                        suggested_dependant_variable_context[design_variable_key][dependant_variable[1]].append(current_context)
    
    # now identify dependent variables as related to requirements via satisfy relationships (to requirement signals)
    for requirement_key in requirement_context.keys():
        suggested_dependant_variable_context[requirement_key] = {}
        requirement =    requirement_context[requirement_key]
        requirement_uid = mission_name + requirement_key
        relationship = 'SATISFY'
        # need to first identify requirement signals for each requirement
        query = """
                    MATCH (requirement:Requirement {uid: '""" + requirement_uid+"""'})-[r:"""+relationship+"""]-(design_element:Design_Element)
                    RETURN design_element,labels(design_element) as labels
        """

        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            design_element_uid = entry['design_element']['uid']
            
            requirement_context[requirement_key][design_element_uid] = {}
            # getting generic types described in variability framework for each design_element
            design_element_types = entry['labels']
            
            for design_element_type in design_element_types:
                current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,design_element_type,design_element_uid,True,graph)
                # add if non empty
                if any(current_context.values()):
                    if not design_element_uid in suggested_dependant_variable_context[requirement_key].keys():
                        suggested_dependant_variable_context[requirement_key][design_element_uid] = current_context

    return suggested_dependant_variable_context

def suggest_requirements_ontology_based(design_variable_context,dependant_variable_context,design_name,variability_framework,query_ontology,graph):    
    suggested_requirement_context    = {}
    for design_variable_key in design_variable_context.keys():
        suggested_requirement_context[design_variable_key] = {}
        design_variable = design_variable_context[design_variable_key]
        design_element_uid = design_name + design_variable_key
        # directly from design model
        query = """
                    MATCH (requirement:Requirement)-[r:PARENT_REQUIREMENT]-(requirement_clause:Requirement_Clause)-[r2:SATISFY]-(requirement_signal:Requirement_Signal)-[r3:SATISFY]-(design_element:Design_Element {uid: '""" + design_element_uid+"""'})
                    RETURN requirement
        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            requirement_uid = entry['requirement']['uid']
            current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,'Requirement',requirement_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                suggested_requirement_context[design_variable_key][requirement_uid] = current_context

    # identify requirements related to all current dependant variables as according to current design model
    for dependant_variable_key in dependant_variable_context.keys():
        suggested_requirement_context[dependant_variable_key] = {}
        dependant_variable = dependant_variable_context[dependant_variable_key]
        dependant_element_uid = design_name + dependant_variable_key
        # directly from design model
        query = """
                    MATCH (requirement:Requirement)-[r:PARENT_REQUIREMENT]-(requirement_clause:Requirement_Clause)-[r2:SATISFY]-(requirement_signal:Requirement_Signal)-[r3:SATISFY]-(design_element:Design_Element {uid: '""" + dependant_element_uid+"""'})
                    RETURN requirement
        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            requirement_uid = entry['requirement']['uid']
            current_context = design_context_framework_query_ontology_based(variability_framework,query_ontology,'Requirement',requirement_uid,True,graph)
            # add if non empty
            if any(current_context.values()):
                suggested_requirement_context[dependant_variable_key][requirement_uid] = current_context

    return suggested_requirement_context

def design_query_via_ontology(variability_framework,query_ontology,design_query:dict,mission_name,design_name,graph):
    # load query ontology
    query_ontology = rdflib.Graph()
    query_ontology.parse("active_framework/query_definition_1.ttl")
    
    # firstly identify role types from query ontology
    query = """
            SELECT DISTINCT ?design_variable_type ?dependant_variable_type ?requirement_type ?active_relationship
            WHERE {
                    :"""+design_query['query type'].replace(' ','_')+""" :DESIGN_VARIABLE_ROLE ?design_variable_type.
                    :"""+design_query['query type'].replace(' ','_')+""" :DEPENDANT_VARIABLE_ROLE ?dependant_variable_type.
                    :"""+design_query['query type'].replace(' ','_')+""" :REQUIREMENT_ROLE ?requirement_type.
                    :"""+design_query['query type'].replace(' ','_')+""" :ACTIVE_RELATIONSHIP ?active_relationship.
        }"""

    outqres = query_ontology.query(query)
    for row in outqres:
        design_variable_type = process_uriref_string(row.design_variable_type)
        dependant_variable_type = process_uriref_string(row.dependant_variable_type)
        requirement_type = process_uriref_string(row.requirement_type)
        active_relationship = process_uriref_string(row.active_relationship)
    
    # collect context information
    # query framework about requirements
    requirement_context = requirement_context_query_ontology_based(design_query,query_ontology,mission_name,variability_framework,query_ontology,graph)
    #interface.show_query_data(requirement_context) 

    # query framework about possible design variables (design elements to be varied)
    design_variable_context = design_variable_context_query_ontology_based(design_query,design_name,variability_framework,query_ontology,graph)

    # identify dependant variables, that exist in design
    dependant_variable_context = dependant_variable_context_query_ontology_based(design_query,design_name,variability_framework,query_ontology,graph)
    
    # now identify dependant variables as dependencies or influenced elements of the selected design variables (only specific types however)
    suggested_dependant_variable_context = suggested_dependant_variables_ontology_based(design_variable_context,requirement_context,design_name,mission_name,variability_framework,query_ontology,graph)

    # now identify suggested design variables as suggest dependent variables that have no dependencies
    suggested_design_variable_context = suggest_design_variables(design_variable_context,suggested_dependant_variable_context,requirement_context,design_name,mission_name,variability_framework,query_ontology,graph)

    # identify requirements related to all current design variables as according to current design model
    suggested_requirement_context  = suggest_requirements_ontology_based(design_variable_context,dependant_variable_context,design_name,variability_framework,query_ontology,graph)

    semi_completed_query = {'query type': design_query['query type'],'requirement':requirement_context,'suggested requirement context':suggested_requirement_context,'design variable':design_variable_context,'dependant variable':dependant_variable_context,'suggested dependant variable':suggested_dependant_variable_context,'suggested design variable':suggested_design_variable_context}
    
    # relevant types that do not exist in current design model
    # this is identified by looking at only specific, local design elements, identified as design variables or dependant variables
    # and selecting their abstract dependencies and children that do no exist in the model 
    completed_query = suggest_additional_design_model_elements(semi_completed_query,variability_framework,query_ontology)
    
        # need deep copy of query dictionary
    filtered_completed_query = copy.deepcopy(completed_query)

    # now need to filter according to current query type
    match design_query['query type']:
        case 'Requirement to Function SA':
            print('r->rd->fd')
            select_types = ['Function']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)
            
            # now further filtering for types relevant to current requirements
            selected_additional_types = {}
            # in this case function fdomains are implicitly related to requirement domains of the same name TODO come up with a formal relationship here
            for type_key in filtered_completed_query['additional model elements']['children'].keys():
                selected_additional_types[type_key] = []

                for additional_element in filtered_completed_query['additional model elements']['children'][type_key]:
                    # identify related requirement if any
                    for req_key in filtered_completed_query['requirement'].keys():
                        for req_type in filtered_completed_query['requirement'][req_key]:
                            if additional_element['additional element'][1].replace('_FDomain','') == req_type.replace('_Domain',''):
                                #print({'type':additional_element['additional element'][1],'relationship':additional_element['additional element'][0],'traceable to':req_key})
                                selected_additional_types[type_key].append({'type':additional_element['additional element'][1],'relationship':additional_element['additional element'][0],'traceable to':req_key})

            # now reassign selected list instead of old
            filtered_completed_query['additional model elements']['children'] = selected_additional_types

        case 'Function to Component SA':
            print('f->fd->cc')
            select_types = ['Subsystem','Unit']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'assigned to components'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework) 
        
        case 'Function to Mode SA':
            print('f->fd->mc')
            select_types = ['Mode']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'grouped_to_modes'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework) 
        
        case 'Functional decomposition SA':
            print('TODO')
            print('f->fd->f')
            select_types = ['FDomain']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'TODO'
            filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)
        
        case 'Internal Interfaces Analysis':
            print('c->cc->cc->c')
            select_types = ['Unit','Subsystem','Spacecraft']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'children',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            relevant_relationship_key = 'interfaces'
            #filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)

        case 'Parametric Analysis':
            print('p->pc->pc->p')
            select_types = ['Parameter']

            # filter for selected types
            filtered_completed_query = filter_additional_types(filtered_completed_query,select_types,'dependencies',variability_framework)

            # now further filtering for types relevant to current functions/requirements
            # relevant relationship between components and functions is
            #relevant_relationship_key = 'grouped_to_modes'
            #filtered_completed_query = select_relevant_additional_types(relevant_relationship_key,filtered_completed_query,variability_framework)

    # Convert and write JSON object to file
    with open("query_result.json", "w") as outfile: 
        json.dump(filtered_completed_query, outfile)

    filtered_completed_query['query type']=filtered_completed_query['query type'].replace(' ','_')

    return filtered_completed_query