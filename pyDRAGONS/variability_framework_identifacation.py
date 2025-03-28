import pandas as pd
from tqdm import tqdm
import variability_framework_tools.variability_framework_textual_core as variability_framework_textual_core
import database_interaction.database_tools as database_tools
import json
from py2neo import Graph
from apyori import apriori
import pprint
import graph_export.graph_plotting as graph_plotting
import variability_framework_tools.rdf_conversion as rdf_conversion
import mapping_definition_1
mapping_module = mapping_definition_1


#####################################################################
# This module provides tools for testing collected differences 
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

def explore_database_perspective(database_entry_type,thing_uid_list,thing_list,relationship_edges,grab_classifier,graph):
    direction_flags_dict = {}
    direction_flags_dict['single'] = True
    
    # first explore outgoing relationships
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
            relationship_edges.append([database_entry_type,entry['relationship_type'],target_type])


    # now exploring incoming relationships
    direction_flags_dict['direction'] = 'INCOMING'
    response = collect_perspective_against_framework(database_entry_type,grab_classifier,direction_flags_dict,graph)
    for entry in response:
        # create thing object of source if new
        if entry['source']['uid'] not in thing_uid_list:
            thing_uid_list.append(entry['source']['uid'])
            thing_list.append(variability_framework_textual_core.Thing(entry['source']['uid'],database_entry_type))
        source_index = thing_uid_list.index(entry['source']['uid'])

        # create thing object of target if new
        target_types =mapping_module.identify_target_types(entry['target_labels'])
        for target_type in target_types:
            if entry['neighbour']['uid'] not in thing_uid_list:
                thing_uid_list.append(entry['neighbour']['uid'])
                thing_list.append(variability_framework_textual_core.Thing(entry['neighbour']['uid'],target_type))

            # need to ensure source and target are right way round
            #print(f"source node is: {entry['relationship_source']['uid']}")
            relationship_edges.append([target_type,entry['relationship_type'],database_entry_type]) # reversed for incoming relationships

    return relationship_edges

def explore_difference_database(labeled_types,thing_uid_list,thing_list,relationship_edges,controlled_flag,graph):
    if controlled_flag:
        # testing comparison direct neighbours
        relationship_edges = explore_database_perspective(labeled_types[0],thing_uid_list,thing_list,relationship_edges,False,graph)

        # testing difference direct neighbours
        relationship_edges = explore_database_perspective(labeled_types[1],thing_uid_list,thing_list,relationship_edges,False,graph)

        # testing value difference direct neighbours
        relationship_edges = explore_database_perspective(labeled_types[2],thing_uid_list,thing_list,relationship_edges,False,graph)

        # testing value difference neighbour classifiers
        relationship_edges = explore_database_perspective(labeled_types[2],thing_uid_list,thing_list,relationship_edges,True,graph)
    else:
        for type in tqdm(labeled_types, colour ='green'):
            # exploring current type and direct neighbours
            #print(f'exploring {type} info')
            relationship_edges = explore_database_perspective(type,thing_uid_list,thing_list,relationship_edges,False,graph)

            # exploring current type and neighbour classifiers
            #relationship_edges = explore_database_perspective(type,thing_uid_list,thing_list,relationship_edges,True,graph)
    
    return relationship_edges

def association_rule_mining_apriori(relationship_edges):
    results = list(apriori(relationship_edges,min_support = 0.0000001,min_confidence = 0.0000001))
    for item in tqdm(results, colour = 'green'):
        # first index of the inner list
        # Contains base item and add item
        pair = item[0] 
        items = [x for x in pair]
        if len(items) == 3:
            pass
            #print("3 Item Rule: " + items[0] + " *->* " + items[1] + " *->* " + items[2])
        elif len(items) == 2:
            pass
            #print("2 Item Rule: " + items[0] + " *->* " + items[1])
        else:
            pass
            #print("Single Item Rule: " + items[0])

        #second index of the inner list
        #print("Support: " + str(item[1]))

        #third index of the list located at 0th
        #of the third index of the inner list

        #print("Confidence: " + str(item[2][0][2]))
        #print("Lift: " + str(item[2][0][3]))
        #print("=====================================")

    return results

def convert_apriori_rules(labeled_types,apriori_results,self_relations_set):
    converted_rules = []
    all_labeled_types = labeled_types + mapping_module.define_mapped_types()
    for item in tqdm(apriori_results, colour='green'):

        # first index of the inner list
        # Contains base item and add item
        pair = item[0] 
        items = [x for x in pair]
        if len(items) == 1:
            if items[0] in all_labeled_types:
                converted_rules.append(f'{items[0]} is Type')

        elif len(items) == 2:
            for s in self_relations_set:
                if set(items) <= s:
                    # identify relationship and self related type
                    for entry in items:
                        if entry in all_labeled_types:
                            source = entry
                        else:
                            identified_relationship = entry
                    
                    converted_rules.append(f'{source} may have relationship of type {identified_relationship} with {source},confidence: {str(item[2][0][2])},lift: {str(item[2][0][3])},support: {str(item[1])}')
                    
                    del source,identified_relationship
                    break
        elif len(items) == 3:
            # need to identify order of rule items
            for entry in items:
                #print(entry)
                if entry in labeled_types:
                    if 'source' in locals():
                        target = entry
                    else:
                        source = entry
                elif entry in all_labeled_types:
                    target = entry
                else:
                    identified_relationship = entry
            try:
                converted_rules.append(f'{source} may have relationship of type {identified_relationship} with {target},confidence: {str(item[2][0][2])},lift: {str(item[2][0][3])},support: {str(item[1])}')
            except Exception as e:
                print('ERROR in identifying target!')
                print(source)
                print(identified_relationship)
                print(items)
                print(e)
                exit(1)
            del source,identified_relationship,target

    return converted_rules

def simplify_rules(rules):
    for rule in rules:
        # need to cycle through type definitions first and then remove duplicate rules from subtypes
        checked_parent_type_list = []             
        if ' is ' in rule:

            # pick new parent type
            parent_name = rule.split('is ')[1]
            if parent_name not in checked_parent_type_list:
                checked_parent_type_list.append(parent_name)

            # find parent related rules
            related_rule_list = []
            for related_rule in rules:
                if 'may' in related_rule and related_rule.split(' ')[0] == parent_name:
                    related_rule_list.append(related_rule.split('may ')[1])

            # find subtypes
            subtype_list = []
            for subtype_definition_rule in rules:
                if ' is ' in subtype_definition_rule:
                    if subtype_definition_rule.split(' is ')[1] == parent_name:
                        identified_subtype = subtype_definition_rule.split(' is ')[0]
                        subtype_list.append(identified_subtype)
                        # remove duplicate subtype rules
                        rule_index = 0
                        while rule_index < len(rules):
                            subtype_rule = rules[rule_index]
                            if 'is' in subtype_rule and subtype_rule.split(' may')[0] == identified_subtype and subtype_rule.split('may ')[1] in related_rule_list:
                                print(f'removing duplicate rule: {subtype_rule} from: {identified_subtype}')
                                print(f' rule was owned by {parent_name}')
                                rules.pop(rule_index)
                                rule_index -= 1
                            rule_index += 1
    return rules
    

def identify_type_hierarchy_via_relationship_rules_(rules):
    # catalogue all types and rules
    types_list = catalogue_types_and_rules (rules)
    # find type hierarchy by shared rules
    for type_key in types_list.keys():
        current_type = types_list[type_key]
        for alternative_type_key in types_list.keys():
            alternative_type = types_list[alternative_type_key]
            if type_key != alternative_type_key:
                # now cycling through rule types and need to check if alternative type includes a sub set, upto full set, of current type
                for rule_type_key in alternative_type.keys():
                    if rule_type_key != 'candidate_subtypes' and rule_type_key != 'subtypes' and rule_type_key != 'parent':
                        alternative_rule_set = alternative_type[rule_type_key]
                        current_rule_set = current_type[rule_type_key]
                        set_alternative_rules = set(alternative_rule_set['relationship'])
                        set_current_rules = set(current_rule_set['relationship'])
                        if not len(set_current_rules) == 0 and not len(set_alternative_rules) == 0:
                            if set_alternative_rules.issubset(set_current_rules):
                                if alternative_type_key not in types_list[type_key]['candidate_subtypes']:
                                    types_list[type_key]['candidate_subtypes'].append(alternative_type_key)
                                    
    # resolve candidate hierarchy, taking number of candidate subtypes as indicator of hierarchy
    # first create list of ordered types by number of candidate subtypes
    subtype_count = 0
    ordered_types_list = []
    while subtype_count <= len(types_list.keys()):
        for type_key in types_list.keys():
            current_type = types_list[type_key]
            if len(types_list[type_key]['candidate_subtypes']) == subtype_count:
                ordered_types_list.append(type_key)
        subtype_count += 1

    #print(f'ordered list is: {ordered_types_list}')
    # now cycle through ordered list to identify hierarchy
    # starting from lowest, where elements that end up belonging to 
    # multiple parents will select only the one of lowest priority,
    # that is higher than their own
    for type_key in ordered_types_list:
        current_type = types_list[type_key]
        # find candidate parents and their priority and pick the one of highest priority, MAY CHANGE TO LOWEST
        # that is higher than current type
        candidate_parent_list = []
        for secondary_type_key in ordered_types_list:
            secondary_current_type = types_list[secondary_type_key]

            if type_key in secondary_current_type['candidate_subtypes']:
                candidate_parent_list.append(secondary_type_key)
            
        # identify priorities
        parent_priority_list = []
        for parent in candidate_parent_list:
            current_parent_priority = ordered_types_list.index(parent)
            if current_parent_priority > ordered_types_list.index(type_key):
                parent_priority_list.append(ordered_types_list.index(parent))
        if parent_priority_list:
            selected_parent = ordered_types_list[max(parent_priority_list)] # changed from min priority -> widest definition structure over deepest
            types_list[type_key]['parent'] = selected_parent
            #print(f'defined parent: {selected_parent} for type: {type_key}')

    # finally add rules for type hierarchy
    rules = add_type_hierarchy_rules(types_list,rules)
    
    return rules

def catalogue_types_and_rules (rules):
    # catalogue all types and rules
    types_list = {}
    for rule in rules:
        if rule.split(' ')[0] not in types_list.keys():
            types_list[rule.split(' ')[0]] = {'permission':{'relationship':[],'second':[]},'prohibition':{'relationship':[],'second':[]},'exclusive':{'relationship':[],'second':[]},'candidate_subtypes':[],'subtypes':[],'parent':'Type'}
        if  'may have relationship of type ' in rule:
            # find matching entry and add permission rule entry
            types_list[rule.split(' ')[0]]['permission']['relationship'].append(rule.split('may have relationship of type ')[1])
            types_list[rule.split(' ')[0]]['permission']['second'].append(rule.split(' with ')[1])
        if ' may not have relationship of type ' in rule:
            # find matching entry and add prohibition rule entry
            types_list[rule.split(' ')[0]]['prohibition']['relationship'].append(rule.split('may not have relationship of type ')[1])
            types_list[rule.split(' ')[0]]['prohibition']['second'].append(rule.split(' with ')[1])
        if ' may only have relationship of type ' in rule:
            # find matching entry and add exclusive rule entry
            types_list[rule.split(' ')[0]]['exclusive']['relationship'].append(rule.split('may only have relationship of type ')[1])
            types_list[rule.split(' ')[0]]['exclusive']['second'].append(rule.split(' with ')[1])
    return types_list

def add_type_hierarchy_rules(types_list,rules):
    for type_key in types_list.keys():
        current_type = types_list[type_key]
        if current_type['parent'] != 'Type':
            rules.insert(rules.index(f'{type_key} is Type')+1,f'{type_key} is {current_type["parent"]}')
            rules.pop(rules.index(f'{type_key} is Type'))
    return rules

def check_relationship_direction(rules,relationship_edges):
    rule_index = 0
    with tqdm(total=len(rules), colour = 'green') as pbar:
        while rule_index < len(rules):
            rule = rules[rule_index]
            # find relational rule
            if ' may ' in rule:
                
                # use relationship_edges records to ensure relational rule is correct way round
                rule_source = rule.split(' may')[0]
                relationship = rule.split('relationship of type ')[1].split(' with')[0]
                mid_section = rule.split(' may ')[1].split(' with')[0]
                rule_target = rule.split('with ')[1].split(',confidence:')[0]
                parameters_section = ',confidence:'+rule.split(',confidence:')[1]

                
                # now check this order against relationship_edges records and if this never occurs, then reverse the rule
                # now check for which directions of this rule occur
                # checking current direction
                edge_reconstruction = [rule_source,relationship,rule_target]
                rule_confirmed = False
                for edge in relationship_edges:
                    if edge_reconstruction == edge:
                        rule_confirmed = True
                        break                

                # adding correct versions of rule, even both if necessary
                if rule_confirmed:
                    # now checking reversed version
                    edge_reconstruction = [rule_target,relationship,rule_source]
                    reversed_rule_confirmed = False
                    for edge in relationship_edges:
                        if edge_reconstruction == edge:
                            reversed_rule_confirmed = True
                            break
                    # add reversed version if confirmed
                    if reversed_rule_confirmed:
                        reversed_rule = f'{rule_target} may {mid_section} with {rule_source}'+parameters_section
                        #print(f'adding reverse rule: {reversed_rule}')
                        # check if the rule version already exists, and add if not
                        if not reversed_rule in rules:
                            rules.insert(rule_index,reversed_rule)
                            rule_index += 1 # need to move one extra index
                else:
                    reversed_rule = f'{rule_target} may {mid_section} with {rule_source}'+parameters_section
                    #print(f'reversing rule, incorrect version is: {rule}')
                    #print(f'corrected version is: {reversed_rule}')
                    rules[rule_index] = reversed_rule
                
            rule_index += 1
            pbar.n = rule_index
            pbar.refresh()
    return rules

def identify_type_hierarchy(include_domains_flag,labeled_types,pure_labels,rules,graph):
    #rules = identify_type_hierarchy_via_relationship_rules_(rules)
    rules = identify_type_hierarchy_via_coincident_labels(include_domains_flag,labeled_types,pure_labels,rules,graph)

    return rules

def identify_type_hierarchy_via_coincident_labels(include_domains_flag,labeled_types,pure_labels,rules,graph):
    types_list = catalogue_types_and_rules (rules)

    type_sets_dict = {}
    for labeled_type in tqdm(labeled_types, colour='green'):
        if (not include_domains_flag and not 'Domain' in labeled_type) or include_domains_flag and labeled_type not in pure_labels:
            query = f"MATCH (n:{labeled_type}) RETURN labels(n)"
            response = database_tools.run_neo_query(['nil'],query,graph)
            type_shared_labels = []
            if response:
                for entry in response:
                    type_shared_labels.extend(entry['labels(n)'])
                
            # only select tracked labels that are not pure labels
            type_tracked_shared_labels = []
            for shared_label in type_shared_labels:
                if shared_label in labeled_types and not shared_label in pure_labels:
                    type_tracked_shared_labels.append(shared_label)
            type_sets_dict[labeled_type] = set(type_tracked_shared_labels)
            
            # now looping over each type set and identifying immediate super class
            # defined as set with least number of coincident but more coincident lables 
            # than current type
            for type_set in type_sets_dict.items():
                selected_type_set = type_set[1]
                # ignore type sets with no members
                if len(selected_type_set) != 0:
                    candidate_superclasses_list = []
                    candidate_superclasses_size_list = []
                    # now finding sets that include this set
                    for candidate_type_set in type_sets_dict.items():
                        selected_candidate_type_set = candidate_type_set[1]
                        if selected_type_set.issubset(selected_candidate_type_set):
                            candidate_superclasses_list.append(candidate_type_set[0])
                            candidate_superclasses_size_list.append(len(selected_candidate_type_set))
                    # now selecting set with minium members that is a super set of current type set
                    # this is done by selecting the second to smallest entry in the set size list
                    # second to smallest as the smallest is the current type set
                    candidate_superclasses_size_list_sorted, candidate_superclasses_list_sorted = zip(*sorted(zip(candidate_superclasses_size_list, candidate_superclasses_list)))
                    # if the type set has one member -> the current type itself, then set 'type' as superclass
                    if type_set[0] =='Function':
                        #print(candidate_superclasses_size_list)
                        #print(candidate_superclasses_list)
                        pass
                    if len(candidate_superclasses_list) == 1:
                        selected_superclass = 'Type'
                        selected_superclass_size = candidate_superclasses_size_list_sorted[0]
                    # in the case where all candidate sets are the same size, need to ensure the super class is not
                    # selected as the current type (leading) to circular hierarchies, therefore select top level -> 
                    # i.e. 'type'
                    # this typically occurs for requirement or function domains
                    elif len(set(candidate_superclasses_size_list)) == 1:
                        selected_superclass = 'Type'
                        selected_superclass_size = candidate_superclasses_size_list_sorted[0]
                    else:
                        # the smallest entry is selected by first sorting the set list and set size list together
                        selected_superclass = candidate_superclasses_list_sorted[1]
                        selected_superclass_size = candidate_superclasses_size_list_sorted[1]
                        # if the second entry happens to be the set size or even the current type (due to sets of the same size), then
                        # then pick the next larger set

                        # if this is a domain, simply select the next type
                        if 'Domain' in type_set[0]:
                            if selected_superclass == type_set[0]:
                                selected_superclass = candidate_superclasses_list_sorted[2]
                        else:
                            # looping until next larger set found
                            select_index = 2
                            while selected_superclass_size == len(selected_type_set):
                                selected_superclass = candidate_superclasses_list_sorted[select_index]
                                selected_superclass_size = candidate_superclasses_size_list_sorted[select_index]
                                select_index += 1

                    # in the case where no rules have been determined for a specific type, need to add a 
                    # catalogued entry and generic rule for this
                    if type_set[0] in types_list.keys():
                        types_list[type_set[0]]['parent'] = selected_superclass
                    else:
                        types_list[type_set[0]] = {'permission':{'relationship':[],'second':[]},'prohibition':{'relationship':[],'second':[]},'exclusive':{'relationship':[],'second':[]},'candidate_subtypes':[],'subtypes':[],'parent':'Type'}
                        rules.append(type_set[0] + ' is Type')

        else:
            # labelling pure label as a label
            for i in range(len(rules)):
                rule = rules[i]
                if ' is ' in rule and rule.split(' is ')[0] in pure_labels:
                    #print(f'correcting label{rule.split(" is ")[0]}')
                    corrected_rule = rule.split(' is ')[0]+ ' is Label'
                    rules[i] = corrected_rule

    rules = add_type_hierarchy_rules(types_list,rules)
    return rules

def check_circular_hierarchy_on_rules(test_type,identifed_super_type_list,is_circular,rules):
    # now find type declaration rule
    for rule in rules:
        if test_type+' is ' in rule and rule.find(test_type+' is ') == 0:
            super_type  =  rule.replace(test_type+' is ','')
            
            if super_type in identifed_super_type_list:
                print(rule)
                print(super_type)
                print(identifed_super_type_list)
                is_circular = True
            elif super_type != 'Type':
                identifed_super_type_list.append(super_type)
                is_circular = check_circular_hierarchy_on_rules(super_type,identifed_super_type_list,is_circular,rules)
                
    return is_circular

def identify_labels(pure_labels,rules):
    print(pure_labels)
    for i in tqdm(range(len(rules)), colour='green'):
        rule = rules[i]
        if ' is ' in rule and rule.split(' is ')[0] in pure_labels:
            print(f'correcting label{rule.split(" is ")[0]}')
            corrected_rule = rule.split(' is ')[0]+ ' is Label'
            rules[i] = corrected_rule

    return rules

def identify_labels_auto(labeled_types,rules):
    identified_labels = []
    for labelled_type in tqdm(labeled_types, colour='green'):
        if check_circular_hierarchy_on_rules(labelled_type,[],False,rules):
            identified_labels.append(labelled_type)

    # now rewrite entry in rules to 'is Label'
    # find rule
    for i in range(len(rules)):
        rule = rules[i]
        if ' is ' in rule and rule.split(' is ')[0] in identified_labels:
            corrected_rule = rule.split(' is ')[0]+ ' is Label'
            rules[i] = corrected_rule
    return rules

def identify_uniqueness_types(labeled_types,rules,graph):
    unique_type_list = []
    for label in labeled_types:
        # query the database for each label type and check it appears more than once in each design
        # if only appears once, assume must be unique
        query = """
                    MATCH (n:"""+label+""") RETURN labels(n)
                """
        response = database_tools.run_neo_query(['nil'],query,graph)
        design_wise_appearance_list = {}
        for row in response:
            design_name = ''
            for returned_label in row['labels(n)']:
                # identify design name label before searching for appearance of current label
                if '_Design_Instance_Element' in returned_label:
                    design_name = returned_label
                    if design_name not in design_wise_appearance_list.keys():
                        design_wise_appearance_list[returned_label]=0
                    break

            # only check for uniqueness if design name has been found
            if design_name != '':
                for searched_label in row['labels(n)']:
                    if searched_label == label:
                        design_wise_appearance_list[design_name] = design_wise_appearance_list[design_name] + 1 

        # now add label to unique list if only appears upto one time in each design  
        unique = True
        for key in design_wise_appearance_list.keys():
            if design_wise_appearance_list[key] > 1:
                unique = False
        if unique == True and design_wise_appearance_list.keys():
            unique_type_list.append(label)       

    # now add uniqueness rules to rule set
    for type in unique_type_list:
        rules.extend([f'{type} must be unique_in_design'])

    return rules
def remove_uniqueness_rules(filter_statement,rules):
    filtered_rules = []
    for rule in rules:
        if filter_statement not in rule:
            filtered_rules.append(rule)
    return filtered_rules

def write_relationship_class(framework_file,relationship_name):
    framework_file.write(f"class {relationship_name}(variability_framework_textual_core.Relationship):\n")
    framework_file.write(" def __init__(self, source, target):\n")
    framework_file.write(f"     super().__init__('{relationship_name}', source, target)\n")
    framework_file.write(" def forbidden(self):\n")
    framework_file.write("     print(f'{self.a.name} tried to have link type "+relationship_name+" with {self.b.name}, but this violates the variability framework...')\n")
    framework_file.write(" def invoke(self):\n")
    framework_file.write("     print(f'{self.a.name} link "+relationship_name+" with {self.b.name}')\n\n")

def write_type_class(framework_file,type_name,parent):
    if parent != 'Type':
        framework_file.write(f"class {type_name}({parent}):\n")
        framework_file.write(" def __init__(self, name, type):\n")
        framework_file.write(f"     super().__init__(name, type)\n")
    else:
        framework_file.write(f"class {type_name}(variability_framework_textual_core.Thing):\n")
        framework_file.write(" def __init__(self, name, type):\n")
        framework_file.write(f"     super().__init__(name, type)\n")

def write_rules_to_framework_file(apriori_rules,filename):
    with open(filename, "w") as framework_file:
        # import statements
        framework_file.write("import variability_framework_textual_core\nimport data_extraction\n\n")
        
        # defining relationship classes
        relationship_name_list = []
        type_name_list = []
        for rule in tqdm(apriori_rules,colour = 'green'):
            if 'may' in rule:
                relationship_name = rule.split('relationship of type ')[1].split(' with')[0]
                if relationship_name not in relationship_name_list:
                    write_relationship_class(framework_file,relationship_name)
                    relationship_name_list.append(relationship_name)
            elif 'is' in rule:
                type_name = rule.split('is ')[0]
                if type_name not in type_name_list:
                    parent_name = rule.split('is ')[1]
                    write_type_class(framework_file,type_name,parent_name)
                    type_name_list.append(type_name)

        # adding the rules
        framework_file.write("def define_framework():\n rules =[\n")
        
        # this method has no support for the confidence parameters etc
        for rule in apriori_rules:
            framework_file.write(f"    '{rule.split(',confidence:')[0]}'\n")

        framework_file.write("  ]\n\n")
        framework_file.write(" relationship_mapping = []\n")
        framework_file.write(" type_mapping = []\n")
        framework_file.write(" return rules, relationship_mapping, type_mapping")

def identify_product_line_features(labeled_types,string_rules,graph):
    # needs comparisons and difference nodes loaded
    # first return all comparison nodes

    query = """
                MATCH (n:Comparison) RETURN n
            """
    comparison_response = database_tools.run_neo_query(['nil'],query,graph)

    feature_types = {}
    for comparison in comparison_response:
        # for each comparison find related design element types and detected differences
        # start with associated design element types
        current_design_element_types = []
        query = """
                MATCH (n:Comparison {uid:'"""+comparison['n']['uid']+"""'})-[:COMPARISON_LOCATION_IN_DESIGN]->(des_element) RETURN labels(des_element) as des_element_labels
            """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            for element_type in entry['des_element_labels']:
                # only add if not already added
                if not element_type in current_design_element_types and element_type in labeled_types:
                    current_design_element_types.append(element_type)
        
        # find differences and associated design element types
        query = """
                MATCH (n:Comparison {uid:'"""+comparison['n']['uid']+"""'})<-[:DISCOVERED_BY]-(difference:Difference) RETURN labels(difference) as difference_labels,difference.Different_Detail as Different_Detail, difference.Base_Design as Base_Design
            """
        response = database_tools.run_neo_query(['nil'],query,graph)
        current_difference_design_element_types = []
        for entry in response:
            for difference_type in entry['difference_labels']:
                # only add if not already added
                if 'Difference_' in difference_type:
                    current_difference_type = difference_type.replace('Difference_','')

            # now record different design element types
            if entry['Different_Detail'] != 'NONE':
                if ' ' in entry['Different_Detail']:
                    data = entry['Different_Detail'].split(' ')[1],entry['Base_Design']
                    if not data in current_difference_design_element_types:
                        current_difference_design_element_types.append(data)
                elif ':' in entry['Different_Detail']:
                    data = entry['Different_Detail'].split(':')[1],entry['Base_Design']
                    if not data in current_difference_design_element_types:
                        current_difference_design_element_types.append(data)
                else:
                    data = entry['Different_Detail'],entry['Base_Design']
                    current_difference_design_element_types = [data]
        
        # find parent comparisons
        current_parent_comps = []
        query = """
                MATCH (n:Comparison {uid:'"""+comparison['n']['uid']+"""'})-[:PARENT_COMPARISON]->(comparison:Comparison) RETURN labels(comparison) as Comparison_labels, comparison
            """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            for comparison_type in entry['Comparison_labels']:
                # only add if not already added
                if not comparison_type.replace('Comparison_','') in current_parent_comps and 'Comparison_' in comparison_type:
                    current_parent_comps.append(comparison_type.replace('Comparison_',''))
        
        # now append arrays to feature_types dict
        for element_type in current_design_element_types:
            if not element_type in feature_types.keys():
                feature_types[element_type] = {'identified differences':{},'feature_ple_types':['mandatory']}
            for entry in current_difference_design_element_types:
                if current_difference_type not in feature_types[element_type]['identified differences'].keys():
                    feature_types[element_type]['identified differences'][current_difference_type] = []
                if entry not in feature_types[element_type]['identified differences'][current_difference_type]:
                    feature_types[element_type]['identified differences'][current_difference_type].append(entry)
        
    # now determine PLE feature types

    # method for identifying mandatory features (i.e. if the feature exists in mission, then it exists in all designs)
    for feature_type_key in feature_types.keys():
        feature_type = feature_types[feature_type_key]
        if 'PARENT' in feature_type['identified differences']:
            for entry in feature_type['identified differences']['PARENT']:
                # as found a parent type difference, can assume this element type is optional
                for optional_feature_type_key in feature_types.keys():
                    if optional_feature_type_key == entry[0] and 'mandatory' in feature_types[optional_feature_type_key]['feature_ple_types']:
                        feature_types[optional_feature_type_key]['feature_ple_types'].remove('mandatory')
                        feature_types[optional_feature_type_key]['feature_ple_types'].append('optional')
   
    # method for identifying  alternatives (i.e.these types never coexist in same design in comparison)
    # not implemented
    """
    for feature_type_key in feature_types.keys():
        feature_type = feature_types[feature_type_key]
        pprint.pprint(feature_types['Spacecraft'])
        exit()
        if 'PARENT' in feature_type['identified differences']:
            # collect all relevant design element types and instances in designs
            design_element_types = {}
            for entry in feature_type['identified differences']['PARENT']:
                if not entry[0] in design_element_types.keys():
                    design_element_types[entry[0]] = []
                design_element_types[entry[0]].append(entry[1])
            
            for design_element_type_key in design_element_types.keys():
                instance_list = design_element_types[design_element_type_key]

                # if a repeat exists does not exist, then is likely an alternative
                pprint.pprint(design_element_types)
                print(instance_list)
                exit()
                if len(instance_list) == len(set(instance_list)):
                    # first need to make sure an entry has been made fo this feature, as if no comparison occurred precisely on this feature, then none will yet exist
                    if design_element_type_key in feature_types.keys():
                    #    feature_types[design_element_type_key] = {'identified differences':{},'feature_ple_types':['mandatory']}
                    # TODO FIX THIS!!!!!!
                        if not 'alternative' in feature_types[design_element_type_key]['feature_ple_types']:
                            feature_types[design_element_type_key]['feature_ple_types'].append('alternative')
                            print(design_element_type_key)
    """
                    
    # now write to rules
    for feature_type_key in feature_types.keys():
        feature_type = feature_types[feature_type_key]
        for ple_type in feature_type['feature_ple_types']:
            string_rules.append(feature_type_key + ' may have relationship of type FEATURE_TYPE with '+ple_type)
    pprint.pprint(string_rules)
    return string_rules

def identify_framework():
    # load the selected mapping module
    labeled_types = mapping_module.define_labelled_types()
    pure_labels = mapping_module.define_pure_labels()

    graph = Graph("bolt://127.0.0.1:7687", auth=('neo4j', 'test'))
    thing_uid_list = []
    thing_list = []
    
    # performing association rule mining
    relationship_edges = []
    print('exploring database')
    relationship_edges = explore_difference_database(labeled_types,thing_uid_list,thing_list,relationship_edges,False,graph)


    # recording self relations for processing later
    self_relations = []
    for edge in relationship_edges:
        if edge[0] == edge[2]:
            self_relations.append(edge)

    self_relations_sets = list(map(set, self_relations))

    print('rule mining')
    apriori_results = association_rule_mining_apriori(relationship_edges)

    # convert to string statement form    
    print('converting rules')
    string_rules = convert_apriori_rules(labeled_types,apriori_results,self_relations_sets)


    # check relationship directions
    print('checking rule direction')
    string_rules = check_relationship_direction(string_rules,relationship_edges)

    # identify type hierarchy
    print('identifying type hierachy')
    string_rules = identify_type_hierarchy(True,labeled_types,pure_labels,string_rules,graph)

    # identify product line features
    string_rules = identify_product_line_features(labeled_types,string_rules,graph)


    # identify labels -> types with circular hierachies
    #print('identifying labels')
    #string_rules = identify_labels(pure_labels,string_rules)

    # identify uniqueness constraints
    #string_rules = identify_uniqueness_types(labeled_types,string_rules,graph)
    # simplify rule set
    #string_rules = simplify_rules(string_rules)

    # remove uniqueness rules for now
    #filtered_string_rules = remove_uniqueness_rules(' must be ',rules)
    # write identified rules to file
    
    print('writing to python based framework file')
    filename = 'active_framework/variability_definition_1.py'
    write_rules_to_framework_file(string_rules,filename)
    #rdf_conversion.convert_to_rdf_class_orientated(string_rules,'rdf_variability_definition_2')

    print('writing to rdf based framework file')
    rdf_conversion.convert_to_rdf_class_orientated(string_rules,'active_framework/rdf_variability_definition_1')

    #graph_plotting.display_variability_framework_ontology(string_rules)
    
def main():
    identify_framework()

if __name__ == '__main__':
    main()
    