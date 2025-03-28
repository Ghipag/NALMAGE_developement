# import pyDRAGONS.design_editing
import sysml
import nalmage.ner_tools
import pprint
import openai
import shutil
import os
import rdflib
import math
import re
from collections import Counter
import nalmage.nalglobals
import pyDRAGONS
import copy
from pyDRAGONS.design_editing import design_edit_tools
from pyDRAGONS.design_problem_formulation import design_problem_query_tools

def take_text_input(question):
    response = input(question+'\n')
    nalmage.ner_tools.logged_print(response)
    return response

def collect_all_component_functions(parent,child):
    component = parent.__getitem__(child)
    function_list =[]
    for mode in component.modes:
        grabbed_mode = component.__getitem__(mode)
        nalmage.ner_tools.logged_print(grabbed_mode)
        for function in grabbed_mode.functions:
            function_list.append(function)            
    return function_list

def collect_all_component_modes(parent,child):
    component = parent.__getitem__(child)
    mode_list =[]
    for mode in component.modes:
        mode_list.append(mode) 
    return mode_list

def collect_all_component_mode_functions(parent,child,mode_name):
    component = parent.__getitem__(child)
    grabbed_mode = component.__getitem__(mode_name)
    function_list =[]
    nalmage.ner_tools.logged_print(grabbed_mode)
    for function in grabbed_mode.functions:
        function_list.append(function)            
    return function_list

def collect_all_component_property_values(parent,child):
    component = parent.__getitem__(child)
    value_list =[]
    for value in component.values:
        value_list.append(value) 
    return value_list

def completion_query(client,prompt,temperature):
    response = client.chat.completions.create(model="gpt-4o",
        messages=prompt,
        temperature=temperature,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0)
    return response

def exchange(client,prompt,context):
    # Set the prompt prefix for the chatbot
    prompt_prefix = "user"
    newprompt = {'role':prompt_prefix,'content':prompt}
    context.append(newprompt)
    # nalmage.ner_tools.logged_print(context)
    response = completion_query(client,context,1)
    nalmage.ner_tools.logged_print(response.choices[0].message.content)
    return {'conversation':context, 'last_completion':response}

def select_conversation(conversation,conversation_list):
    if conversation != '':
        conversation_input = take_text_input('Do you wish to continue the ongoing conversation? (Y/n)')
        if conversation_input == 'Y' or conversation_input == 'y':
            conversation = conversation
        else:
            conversation_list.append(conversation)
            i = 0
            for conversation in conversation_list:
                nalmage.ner_tools.logged_print(i)
                nalmage.ner_tools.plogged_print(conversation)
                i = i + 1
            conversation_input = take_text_input('which conversation do you wish to switch to? (if none hit RETURN else enter ID)')
            if conversation_input != '':
                conversation = conversation_list[int(conversation_input)]
            else:
                conversation = ''

    return conversation,conversation_list

def select_element_generation_type():
    # Set the list of available element types
    element_types = ['Subsystems','Components','Loose Modes (without directly owned functions)','Rigorous Modes (with owned functions)','Functions','SubFunctions','Values','Interfaces'] 
    i = 0
    for type in element_types:
        nalmage.ner_tools.logged_print(i)
        nalmage.ner_tools.plogged_print(type)
        i = i + 1
    type_input = take_text_input('what type of model element do you wish to generate? (enter id)')
    return element_types[int(type_input)]

def prompt_for_elements(client,prompt_input,conversation,down_selection):
    prompt = exchange(client,prompt_input,conversation)
    conversation = prompt['conversation'] 
    # nalmage.ner_tools.logged_print(conversation)

    nalmage.ner_tools.identify_named_elements(prompt['last_completion'].choices[0].message.content.strip())
    elements = nalmage.ner_tools.identify_bulleted_list(prompt['last_completion'].choices[0].message.content.strip())

    print(f'bulleted list: {elements}')

    identified_elements = []
    for element in elements['elements']:
        identified_elements.append(nalmage.ner_tools.identify_formatted_elements(element))

    #now allowing the user to delete unwanted elements
    nalmage.ner_tools.logged_print('***\nThe following candidate system elements have been identified:\n***')
    i = 0
    for element in identified_elements:
        nalmage.ner_tools.logged_print(i)
        nalmage.ner_tools.plogged_print(element)
        i = i + 1

    del_element_ids = ''
    if down_selection:
        del_element_ids = take_text_input('***\nEnter the element numbers to be deleted (in the form [id1,id2,id3.....]), or re-prompt with "r":\n***').replace('[','').replace(']','').split(',')
        if 'r' in del_element_ids:
            prompt_input = take_text_input('enter your feedback for the language model')
            del_element_ids,identified_elements,conversation = prompt_for_elements(client,prompt_input,conversation,down_selection)
    return del_element_ids,identified_elements,conversation

def prompt_llm_for_elements(feedback_flag,client,conversation,generate_type,root_element,reduced_design_rules_string,reference_type,reference_element_string,query_returned_results,format_string):
    manual_method = False
    down_selection = True
    if manual_method:
        nalmage.ner_tools.logged_print('prompts should mention Sysml Model and ask for lists, typically with - bullet points')
        nalmage.ner_tools.logged_print('when asking for logical/physical elements prompts should ask for subsystems or components etc.')
        nalmage.ner_tools.logged_print('when asking for parameters prompts should ask for parameters etc.')
        prompt_input = take_text_input('enter your prompt for the language model')
    else:
        reference_element_info = 'that are traceable to these ' + reference_type +':'+ reference_element_string
        if generate_type == 'Interfaces':
            reference_element_info = 'of type: '+ reference_element_string + ' with  other ' + reference_type
        prompt_input =  "With no preamble or post amble text, given the following rdf definition of a " + root_element[2] + ", suggest a set of " + generate_type + "s " + reference_element_info + "\n RDF " + root_element[2] + " definition:\n" +reduced_design_rules_string +"\n note that you should use the format " + format_string + " with new lines between each"
        if query_returned_results:
            if generate_type == 'Functions':
                prompt_input = prompt_input +'\n and the suggested functions have meaningful names, be labelled with some subset from the following list:\n' + str(query_returned_results)
            else:
                prompt_input = prompt_input +'\n and the suggested elements should be a sub set of the following allowed types:\n' + str(query_returned_results)

    nalmage.ner_tools.logged_print(prompt_input)
    # querying LLM model
    del_element_ids,identified_elements,conversation = prompt_for_elements(client,prompt_input,conversation,down_selection)
   
    selected_elements = []
    for i in range(len(identified_elements)):
        if str(i) not in del_element_ids:
            selected_elements.append(identified_elements[i])
    
    nalmage.ner_tools.logged_print('***\nYou have selected the following elements:\n***')
    nalmage.ner_tools.plogged_print(selected_elements)

    if feedback_flag:
        feedback_pompt = 'rate out of 3 the traceability of these '+ generate_type +' to their related '+ reference_type +', in the format {[element you suggested]:[score out of 3]}'
        nalmage.ner_tools.logged_print(feedback_pompt)
        prompt = exchange(client,feedback_pompt,conversation)
        conversation = prompt['conversation'] 
        # print(f"last completion is {prompt['last_completion'].choices[0].message.content.strip()}")
        ratings = nalmage.ner_tools.identify_bulleted_list(prompt['last_completion'].choices[0].message.content.strip())
        identified_ratings = []
        for rating in ratings['elements']:
            identified_ratings.append(nalmage.ner_tools.identify_formatted_elements(rating))

        rating_element_list = []
        for rating in identified_ratings:
            rating_element_list.append(rating["element"])
            # print(f'rating for {rating["element"]} is {rating["traceable/interfaced type"]}')
        
        # now linking rating to selected_element
        updated_selected_elements = []
        # print(selected_elements)
        for element in selected_elements:
            related_selected_element = cosine_simarlity_classifier_selection(element['element'],rating_element_list)
            print(f"selected element for {element['element']}: {related_selected_element}")
            for rating in identified_ratings:
                if rating['element'] == related_selected_element:
                    updated_selected_elements.append({'element':element['element'],'traceable/interfaced type':element['traceable/interfaced type'],'rating':rating['traceable/interfaced type']})
        selected_elements = updated_selected_elements

    return selected_elements, conversation

def generate_elements(root_element,mission_name,element_list,selected_elements,design_data,design_name,super_types,reference_element_list,query_returned_results,graph,variability_framework):
    # now generating blocks (or components) for identified elements
    for element in selected_elements:

        element_name = element['element']
        classifier, subclasses = classifier_selection(element_name,super_types,query_returned_results,variability_framework)
        reference_entry = reference_element_selection(element['traceable/interfaced type'],design_data,mission_name,graph)
        subclasses_entry = 'NONE'
        if 'Function' in super_types:
            subclasses_entry = ''
            for sub in subclasses:
                subclasses_entry = sub + ';'
            subclasses_entry = subclasses_entry[:-1]
        print(subclasses_entry)
        data_entry = [element_name,classifier, 'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	1,subclasses_entry,'NONE','NONE',	'NONE','NONE','NONE','NONE',reference_entry]
        if 'rating' in element.keys():
            data_entry.append(element['rating'])
        else:
            data_entry.append('NONE')
        design_data.loc[len(design_data)] = data_entry
        design_data.drop_duplicates() # possible error here
        # design_data = nalmage.model_generation.copy_and_squash_design_data(design_name,design_data)
        design_data.to_csv(f"./data/{design_name}_info.csv", index=False)

        # update ownership
        parent_name = root_element[1]
        design_edit_tools.add_element_ownership(element_name,parent_name,design_data,design_name)

        # update element list
        element_list.append([len(element_list),element['element'],classifier])
    
    # now refresh model in database
    design_edit_tools.refresh_model_in_data_based(design_name,design_data,mission_name,graph)

    return design_data,element_list

def generate_relationships(design_variable,mission_name,element_list,selected_elements,design_data,design_name,query_returned_results,graph):
    # now generating blocks (or components) for identified elements
    for element in selected_elements:

        element_name_text = element['element']
        element_name = reference_element_selection(element_name_text,design_data,mission_name,graph)
        interface_type_text = element['traceable/interfaced type'].replace('_',' ').lower() # bit of processing to help cosine similarity 
        interface_type = interface_type_selection(interface_type_text,['power interfaces','data interfaces','mechanical interfaces','fluid interfaces','thermal interfaces'])
        interface_type = interface_type.replace(' ','_')
        print(f'selected interface {interface_type}')
        print(element_name)

        # filter for interfaces in Knowledge Base
        if element_name in query_returned_results:
            print(f'yes: {element_name},{interface_type}')
            design_edit_tools.add_interface(element_name,interface_type,design_variable,design_data,design_name)
            design_data.to_csv(f"./data/{design_name}_info.csv", index=False)

    # now refresh model in database
    design_edit_tools.refresh_model_in_data_based(design_name,design_data,mission_name,graph)

    return design_data,element_list

def generate_blocks(root_element,mission_name,element_list,selected_elements,design_data,design_name,graph,variability_framework):
    # now generating elements for identified elements
    for element in selected_elements:

        component_name = element['element']
        classifier, subclasses = classifier_selection(component_name,['Subsystem','Unit','Spacecraft'],variability_framework)
        design_data.loc[len(design_data)] = [component_name,classifier, 'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	1,'NONE','NONE','NONE',	'NONE','NONE','NONE','NONE']
        design_data.to_csv(f"./data/{design_name}_info.csv", index=False)

        # update ownership
        parent_name = root_element[1]
        design_edit_tools.add_element_ownership(component_name,parent_name,design_data,design_name)

        # update element list
        element_list.append([len(element_list),element])
    
    # now refresh model in database
    design_edit_tools.refresh_model_in_data_based(design_name,design_data,mission_name,graph)

    return design_data,element_list

def generate_value_properties(root_element,element_list,selected_elements):
    # now generating SyML value names for identified elements
    value_names = []
    for element in selected_elements:
        value_name = element['element']
        value_names.append(value_name)
        element_list.append(value_name)

    # add values to current block
    for value_name in value_names:
        root_element.values[value_name]=''

    return root_element,element_list

def generate_modes(root_element,element_list,selected_elements):
    # now generating SyML modes for identified elements
    modes = []
    for element in selected_elements:
        mode = sysml.Mode(element['element'])
        modes.append(mode)
        element_list.append(mode)

    # add modes to current block
    for mode in modes:
        root_element.add_mode(mode.name,mode)

    return root_element,element_list
def group_functions_into_modes(root_element,element_list,selected_elements):
    # get list of grouped functions from user
    i = 0
    for element in element_list:
        nalmage.ner_tools.logged_print(i)
        nalmage.ner_tools.plogged_print(element)
        i = i + 1
    nalmage.ner_tools.logged_print('\n***')
    grouped_function_ids = take_text_input('***\nEnter the element numbers of the functions to be grouped (in the form [id1,id2,id3.....]):\n***').replace('[','').replace(']','').split(',')

    selected_functions = []
    for i in range(len(element_list)):
        if str(i) in grouped_function_ids:
            selected_functions.append(element_list[i])

    nalmage.ner_tools.logged_print('***\nThe following functions will be grouped into modes:\n***')
    nalmage.ner_tools.plogged_print(selected_functions)
    nalmage.ner_tools.logged_print('***\n')
    # now generating SyML modes for identified elements
    modes = []
    for element in selected_elements:
        mode = sysml.Mode(element['element'])
        # identifying functions to add to mode
        for function in selected_functions:
            if function.name in element['text'] or function.name in element['element'] or function.name in element['children']:
                mode.add_function(function.name,function)
                nalmage.ner_tools.logged_print(f'added {function.name} to {mode.name}')
        modes.append(mode)
        element_list.append(mode)

    # add modes to current block
    for mode in modes:
        root_element.add_mode(mode.name,mode)

    # prompt for missed function groupings in post processing of language mdoel response
    correct_flag_input = take_text_input('***\nDo you wish to correct this grouping?(Y/n)\n***')
    while correct_flag_input == 'Y' or correct_flag_input == 'y':   
        i = 0
        for element in element_list:
            nalmage.ner_tools.logged_print(i)
            nalmage.ner_tools.plogged_print(element)
            i = i + 1
        nalmage.ner_tools.logged_print('\n***')
        mode_id=take_text_input('***\nEnter the mode you wish to add functions to\n***').replace('[','').replace(']','').split(',')
        selected_mode = element_list[int(mode_id[0])]
        nalmage.ner_tools.logged_print('\n***')
        function_ids=take_text_input('***\nEnter the function ids you wish to add to selected mode\n***').replace('[','').replace(']','').split(',')
        for function_id in function_ids:
            selected_function = element_list[int(function_id)]
            selected_mode.add_function(selected_function.name,selected_function)
        # prompt for continued corrections
        correct_flag_input = take_text_input('***\nDo you wish to continue corrections?(Y/n)\n***')
    return root_element,element_list

def generate_functions(model,root_element,next_element,element_list,selected_elements):
    # now generating SyML functions for identified elements
    functions = []
    for element in selected_elements:
        function = sysml.Function(element['element'])
        functions.append(function)
        \

    # this function may be used in three scenarios; when adding to a package, when adding to (decomposing) a function and when adding directly to a mode
    # need to check what scenario this is
    if str(type(root_element)) == "<class 'sysml.elements.structure.Mode'>":
        #add new package
        element_list.append(sysml.Package(next_element.name+'_functions'))
        model.add(element_list[-1])

        # add functions to current package
        for function in functions:
            element_list[-1].add(function)

        # add functions to current mode
        for function in functions:
            root_element.add_function(function.name,function)

    elif str(type(root_element)) == "<class 'sysml.elements.structure.Package'>":
        # add functions to current package
        for function in functions:
            root_element.add(function)

    elif str(type(root_element)) == "<class 'sysml.elements.structure.Function'>":
        # add functions to current package
        for function in functions:
            root_element.add_subfunction(function.name,function)

    else:
        nalmage.ner_tools.logged_print('wrong type of root element to add function too')
        nalmage.ner_tools.logged_print(f'root element: {root_element}')
        nalmage.ner_tools.logged_print(f'root element type: {str(type(root_element))}')
        raise TypeError
       
    return model,root_element,element_list

def generate_capella_yaml_dec(parent,child,capella_model,output_file_name):
    if str(type(parent)) == "<class 'sysml.elements.structure.Package'>":
        capella_parent = capella_model.la.root_component
    else:
        capella_parent = capella_model.la.all_components.by_name(parent.name)
    model_yaml_update = f"""
- parent: !uuid {capella_parent.uuid}
  extend:
    components:"""
    model_yaml_update= model_yaml_update + f'\n       - name: {parent.__getitem__(child).name}'
    nalmage.ner_tools.logged_print(f'capella declaration:\n {model_yaml_update}')
    # now output completed yaml file
    with open(output_file_name, "w") as f:
        f.write(model_yaml_update)

    # execute yaml declaration in model
    decl.apply(capella_model,output_file_name)


    capella_model.save()
    return capella_model

def generate_capella_pkg(parent,child,capella_parent_lc):
    pkg_name = parent.__getitem__(child).name
    #generating logical component package to store logical component parts
    lc_pkg = LogicalComponentPkg()
    lc_pkg.set_name(f'{pkg_name}_pkg')
    nalmage.ner_tools.logged_print('created logical component package')
    
    #add the new logical Component to its parent
    capella_parent_lc.get_owned_logical_component_pkgs().add(lc_pkg)
    return capella_parent_lc

def generate_capella_lc(parent,child,capella_parent_lc):
    # create a logical component
    lc = LogicalComponent()
    #set its name
    lc_name = parent.__getitem__(child).name
    nalmage.ner_tools.logged_print("* Create a new logical component with name " + lc_name)
    lc.set_name(lc_name)
    #add the new PhysicalComponent
    capella_parent_lc.get_owned_logical_components().add(lc)

    java_part = create_e_object("http://www.polarsys.org/capella/core/cs/" + capella_version(), "Part")
    java_part.setName(lc_name)
    java_part.setAbstractType(lc.get_java_object())
    nalmage.ner_tools.logged_print('created logical component part')
    
    #generating logical component package to store logical component part
    lc_pkg = LogicalComponentPkg()
    lc_pkg.set_name(f'{lc_name}_pkg')
    nalmage.ner_tools.logged_print('created logical component package')
    
    #add the new logical Component to its parent
    lc_pkg.get_owned_logical_components().add(lc)
    lc_pkg.get_java_object().getOwnedParts().add(java_part)
    capella_parent_lc.get_owned_logical_component_pkgs().add(lc_pkg)
    return capella_parent_lc

def traverse_model_tree(model_section,capella_section):
    for element in model_section.elements:
        grabbed_element = model_section.__getitem__(element)
        nalmage.ner_tools.logged_print(grabbed_element)
        nalmage.ner_tools.logged_print(str(type(grabbed_element)))
        if str(type(grabbed_element)) == "<class 'sysml.elements.structure.Package'>":
            capella_section = generate_capella_pkg(model_section,element,capella_section)  
            traverse_model_tree(grabbed_element,capella_section)
        elif str(type(grabbed_element)) == "<class 'sysml.elements.structure.Block'>":
            capella_section = generate_capella_lc(model_section,element,capella_section)    
            
    return model_section

def clean_capella_project(clean_project_name,working_project_name):
    # overwriting capella project with standard blank one
    shutil.rmtree(f'tool_integration/capella/{working_project_name}') 
    shutil.copytree(f'tool_integration/blank-capella-project/{clean_project_name}', f'tool_integration/capella/{working_project_name}')

def run_capella_corrections():    
    os.system('C:/Users/lt17550/capella/capella/capellac.exe -nosplash -consolelog -application org.polarsys.capella.core.commandline.core -appid org.eclipse.python4capella.commandline -data "C:/Users/lt17550/University of Bristol/grp-Louis-Timperley-PhD - General/Natural Language Case Study/tool_integration/capella" workspace:/Model_Generation_Tools/scripts/model_correction.py')
    
def convert_to_cappella_model(sysml_model,capella_model,output_file_name):
    # firstly overwriting capella project with standard blank one
    clean_capella_project('blank_project','blank_project')

    # gets the SystemEngineering
    se = capella_model.get_system_engineering()
    
    # get the root logical component
    la_ls = se.get_logical_architecture().get_logical_system()
    
    # get the logical component package
    la_cp = se.get_logical_architecture().get_logical_component_pkg()
    
    # start a transaction to modify the Capella model
    capella_model.start_transaction()
    try:
        la_ls = traverse_model_tree(sysml_model,la_ls)  
        nalmage.ner_tools.logged_print('completed model tree')          
    except:
        # if something went wrong we rollback the transaction
        capella_model.rollback_transaction()
        raise
    else:
        # if everything is ok we commit the transaction
        capella_model.commit_transaction()
    
    # save the Capella model
    capella_model.save()
    # get the rootlogicalComponent
    for lc in la_ls.get_owned_logical_components():
        nalmage.ner_tools.logged_print(f'logical components owned by the logical system: {lc.get_name()}')

def manual_classifier_selection(element_name,candidate_classifiers):
    nalmage.ner_tools.logged_print(f'***\nEnter the id of the classifier you wish to select for {element_name}:\n***')
    i = 0
    for candidate_classifier in candidate_classifiers:
        nalmage.ner_tools.logged_print(i)
        nalmage.ner_tools.plogged_print(candidate_classifier)
        i = i + 1
    nalmage.ner_tools.logged_print('\n***')
    classifier = candidate_classifiers[int(take_text_input(''))]
    return classifier

def get_cosine(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in list(vec1.keys())])
    sum2 = sum([vec2[x] ** 2 for x in list(vec2.keys())])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator
        
def text_to_vector(text):
    WORD = re.compile(r"\w+")
    words = WORD.findall(text)
    return Counter(words)

def cosine_simarlity_classifier_selection(element_name,candidate_classifiers):
    vector1 = text_to_vector(element_name.replace('_',' '))
    cosine_scores = []
    for candidate_classifier in candidate_classifiers:
        vector2 = text_to_vector(candidate_classifier.replace('_',' '))
        cosine_scores.append(get_cosine(vector1, vector2))

    # now find closest
    m_cosine = max(cosine_scores)
    selected_candidate = candidate_classifiers[cosine_scores.index(m_cosine)]
    return selected_candidate

def generate_reduced_design_rule_set(parent,variability_framework):

    reduced_design_rules = rdflib.Graph()

    for s, p, o in variability_framework.triples((None, None, parent)):
        reduced_design_rules.add((s,p,o))

    for s, p, o in variability_framework.triples((parent, None, None)):
        reduced_design_rules.add((s,p,o))
    
    reduced_design_rules.serialize(destination="reduced_design_rules.ttl")

    # open open the .ttl file and return contents
    reduced_design_rules_string = ''
    with open('reduced_design_rules.ttl', 'r') as fh:
        for line in fh:
            reduced_design_rules_string = reduced_design_rules_string + line
    
    return reduced_design_rules_string

def classifier_selection(element_name,super_types,query_returned_results,variability_framework):
    candidate_subclasses_classifiers = []
    debug = True
    for super_type in super_types:
        subclass_list,circular_detected = design_problem_query_tools.identify_sub_classes({'classifier':super_type},[],variability_framework,debug)
        
        candidate_subclasses_classifiers.extend(subclass_list)

    # need to split classifiers (types) and subclasses (labels)
    # explore this
    candidate_subclasses_classifiers = query_returned_results # for using the query result to filter classifiers

    candidate_classifiers = []
    candidate_labels = []
    for entry in candidate_subclasses_classifiers:
        if 'Domain' in entry:
            candidate_labels.append(entry)
        else:
            candidate_classifiers.append(entry)


    # classifier = manual_classifier_selection(element_name,candidate_classifiers)
    # handling case for functions when classifier is only function and subclasses (labels) are more important
    if candidate_classifiers:
        classifier = cosine_simarlity_classifier_selection(element_name,candidate_classifiers)
    else:
        classifier = super_types[0]
    if candidate_labels:
        subclass = cosine_simarlity_classifier_selection(element_name,candidate_labels)
    else:
        subclass  = super_types[0]
    

    return classifier, [subclass]

def reference_element_selection(reference_entry,design_data,mission_name,graph):
    candidate_references = list(design_data['name'])
    requirement_names = design_edit_tools.list_requirements(mission_name,False,graph)
    requirement_names_processed = []
    for name in requirement_names:
        requirement_names_processed.append(name.replace('-',''))
    candidate_references.extend(requirement_names_processed)
    reference = cosine_simarlity_classifier_selection(reference_entry,candidate_references)
    return reference

def interface_type_selection(reference_entry,grab_relationship_types):
    interface_type = cosine_simarlity_classifier_selection(reference_entry,grab_relationship_types)
    return interface_type

def copy_and_squash_design_data(design_name,design_data):
    design_data_squashed = copy.deepcopy(design_data)

    #find repeated rows list
    # make names list
    names_list = []
    for index, row in design_data_squashed.iterrows():
        names_list.append(row['name'])
    names_set = set(names_list)
    # now loop over names and squash
    stop = 0
    for name in names_set:
        # find traceable elements
        traceable_elements = design_data_squashed.loc[design_data_squashed['name'] == name,'traceable_to'].values
        traceable_elements = traceable_elements
        
        # now set the traceable elements entry to this as a string
        traceable_elements_string = ''
        for entry in traceable_elements:
            traceable_elements_string = traceable_elements_string + entry + ';'
        traceable_elements_string = traceable_elements_string[:-1]
        design_data_squashed.loc[design_data_squashed['name'] == name,'traceable_to'] =  traceable_elements_string

        del traceable_elements # strange behaviour here
        del traceable_elements_string
        # design_data.loc[design_data['name'] == element_name, 'sub_class'] = design_data.loc[design_data['name'] == element_name, 'sub_class'].replace('NONE','')+';'+candidate_type
        design_data_squashed = design_data_squashed.drop_duplicates()
    
    # now create unsquashed spare and return squashed version
    design_data.to_csv(f"./data/{design_name}_for_rating_info.csv", index=False)
    return design_data_squashed