import pyDRAGONS.database_interaction.data_extraction as data_extraction
import pandas as pd
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
from py2neo import Graph
import pyDRAGONS
import pyDRAGONS.database_interaction.database_tools as database_tools

def assign_type(element_name,candidate_type,design_data,design_name,classifier,component_data):
    """
    Assign a type to an element and update the ontology accordingly.

    Parameters:
    - element_name (str): The name of the element to assign the type to.
    - candidate_type (str): The type to assign to the element.
    - design_data (DataFrame): DataFrame containing design data.
    - design_name (str): The name of the design.
    - classifier (str): The classifier associated with the element.
    - component_data (DataFrame): DataFrame containing component data.

    Returns:
    None

    This function assigns a specified type to a given element and updates the associated design
    data and ontology with the new type information.

    It performs the following steps:
    1. Checks if the 'sub_class' column exists in the design data, if not, adds it with 'NONE' values.
    2. Assigns the candidate type to the element if it is not already assigned.
    3. Updates the ontology with the allowed subtypes for the classifier.
    4. Saves the updated design data and component data to CSV files.

    Note:
    - The 'design_data' DataFrame should contain information about design elements.
    - The 'component_data' DataFrame should contain ontology information about components.
    - Both 'design_data' and 'component_data' are expected to be saved as CSV files.
    - The function updates the CSV files in the './data/' directory.

    Example usage:
    ```
    assign_type("ElementX", "TypeY", design_data, "DesignA", "ClassifierZ", component_data)
    ```

    """
    if 'sub_class' not in design_data.columns:
        design_data=design_data.assign(sub_class='NONE')
    if candidate_type not in str(design_data.loc[design_data['name'] == element_name, 'sub_class']):
        design_data.loc[design_data['name'] == element_name, 'sub_class'] = design_data.loc[design_data['name'] == element_name, 'sub_class'].replace('NONE','')+';'+candidate_type,
        design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
    else:
        print('not repeating label')
    # update ontology with allowed sub class
    existing_allowed_subtypes = component_data.loc[ component_data['name'] == classifier, 'allowed_sub_class']
    if candidate_type not in existing_allowed_subtypes:
        component_data.loc[ component_data['name'] == classifier, 'allowed_sub_class'] = existing_allowed_subtypes + ';' + candidate_type  
    component_data.to_csv("./data/Components_info.csv", index=False)

def add_interface(element_name,interface_type,source_element,design_data,design_name):
    existing_relevant_interfaces = design_data.loc[design_data['name'] == element_name, interface_type]
    delimiter = ';'
    if existing_relevant_interfaces.item() == 'NONE':
        delimiter = ''
    
    if element_name not in existing_relevant_interfaces:
        design_data.loc[design_data['name'] == element_name, interface_type] = design_data.loc[design_data['name'] == element_name, interface_type].replace('NONE','')+delimiter+source_element,
        design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
    else:
        print('not repeating label')

    print(element_name,interface_type,source_element)

def edit_design_subclasses(design_name,component_data):
    """
    Edit subclasses of elements in a design and update the ontology.

    Parameters:
    - design_name (str): The name of the design.
    - component_data (DataFrame): DataFrame containing ontology information about components.

    Returns:
    None

    This function allows for the editing of subclasses of elements in a design and updates
    the associated design data and ontology accordingly.

    It performs the following steps:
    1. Reads design data from a file using the provided design name.
    2. Iterates over each element in the design data.
    3. Identifies candidate types based on element names and classifiers.
    4. Prompts the user to accept the candidate type, suggest an alternative, or avoid.
    5. Calls the 'assign_type' function to assign or suggest the type and update the ontology.
    6. Prints the updated design data.

    Note:
    - The design data is expected to be saved as a CSV file.
    - The component data DataFrame should contain ontology information about components.
    - Both design data and component data are expected to be saved in the './data/' directory.

    Example usage:
    ```
    edit_design_subclasses("DesignA", component_data)
    ```

    """
    design_data = data_extraction.read_data(design_name)

    for index, row in design_data.iterrows():
        # first use element name to identify candidate types
        candidate_type = ''
        if row['classifier'] in row['name']:
            candidate_type = row['name'].replace(row['classifier'],'')
        if candidate_type != '' and candidate_type != 's':
            # trim type string if necessary
            if candidate_type[-1] == '_':
                candidate_type = candidate_type[:len(candidate_type)-1]
            print(f'current element: {Fore.RED}{row["name"]}{Style.RESET_ALL}')
            print(f'existing subclasses: {Fore.CYAN}{row["sub_class"]}{Style.RESET_ALL}')
            response = input(f'accept candidate?:{Fore.GREEN}{candidate_type}{Style.RESET_ALL} (y to accept s to suggest or n to avoid)')
            if response == 'y':
                assign_type(row['name'],candidate_type,design_data,design_name,row['classifier'],component_data)
            elif response == 's':
                response = input(f'suggest alternative: {Fore.BLUE}')
                print(f'{Style.RESET_ALL}')
                candidate_type = response
                assign_type(row['name'],candidate_type,design_data,design_name,row['classifier'],component_data)

    print(design_data)

def list_requirements(mission_name,grab_text,graph):
    """
    List all requirements from the provided mission data.

    Parameters:
    
    Returns:
 

    """
    requirement_text_list = []

    query = """
            MATCH(n:Requirement) RETURN n
            """
    
    requirements_response = database_tools.run_neo_query(['nil'],query,graph)
    for entry in requirements_response:
        if grab_text:
            requirement_text_list.append(entry['n']['name'] + ' -- ' + entry['n']['Text'])
        else:
            requirement_text_list.append(entry['n']['name'])

    return requirement_text_list

def list_components(design_name,graph):
    """
    List all requirements from the provided mission data.

    Parameters:
    
    Returns:
 

    """
    components_list = []

    query = """
            MATCH(n:Unit) RETURN n
            """
    
    components_response = database_tools.run_neo_query(['nil'],query,graph)
    for entry in components_response:
        components_list.append(entry['n']['name'])

    return components_list

def list_functions(design_data):
    """
    List all functions from the provided design data.

    Parameters:
    - design_data (DataFrame): DataFrame containing design data.

    Returns:
    list: A list of function names.

    This function extracts and returns a list of all functions from the provided design data.

    It iterates through the 'name' and 'classifier' columns of the design data and appends
    the names of elements classified as 'Function' to the 'function_list'.

    Note:
    - The 'design_data' DataFrame should contain information about design elements.
    - The 'classifier' column is expected to classify elements as 'Function' or not.

    Example usage:
    ```
    function_list = list_functions(design_data)
    ```

    """
    function_list = []
    for element, element_classifier in zip(design_data['name'], design_data['classifier']):
        if element_classifier == 'Function':
            function_list.append(element)

    return function_list

def list_modes(design_data,mode_data):
    """
    List all modes from the provided design data based on mode classifiers.

    Parameters:
    - design_data (DataFrame): DataFrame containing design data.
    - mode_data (DataFrame): DataFrame containing mode information.

    Returns:
    list: A list of tuples containing mode indices and their corresponding names.

    This function extracts and returns a list of modes from the provided design data
    based on mode classifiers provided in the mode data.

    It iterates through the 'name' and 'classifier' columns of the design data and checks
    if the element classifier matches any of the mode classifiers provided in the mode data.
    If a match is found, it appends a tuple containing the mode index and the element name
    to the 'mode_list'.

    Note:
    - The 'design_data' DataFrame should contain information about design elements.
    - The 'classifier' column is expected to classify elements.
    - The 'mode_data' DataFrame should contain mode information including mode classifiers.

    Example usage:
    ```
    mode_list = list_modes(design_data, mode_data)
    ```

    """
    mode_list = []
    mode_classifiers = mode_data['name'].values.tolist()
    for element, element_classifier in zip(design_data['name'], design_data['classifier']):
        if element_classifier in mode_classifiers:
            mode_list.append([len(mode_list),element])

    return mode_list


def edit_design_functions(design_name,missions,mode_data,component_data):
    """
    Edit functions in a design based on mission requirements and mode data.

    Parameters:
    - design_name (str): The name of the design.
    - missions (dict): A dictionary mapping mission names to their associated designs.
    - mode_data (DataFrame): DataFrame containing mode information.
    - component_data (DataFrame): DataFrame containing component data.

    Returns:
    None

    This function allows for the editing of functions in a design based on mission requirements
    and mode data. It adds new functions or links existing functions to requirements.

    It performs the following steps:
    1. Identifies the mission name associated with the design.
    2. Reads design and requirement data from files using the provided names.
    3. Iterates through each requirement and proposes new or existing functions based on functionality.
    4. Adds new functions to the design if chosen by the user and updates the design data.
    5. Identifies modes with no grouped function and generates notional functions for them.
    6. Adds notional functions to the design and updates the design data.

    Note:
    - The design data is expected to be saved as a CSV file.
    - The mission data should be a dictionary mapping mission names to associated designs.
    - The mode data DataFrame should contain information about modes.
    - The component data DataFrame should contain ontology information about components.

    Example usage:
    ```
    edit_design_functions("DesignA", missions, mode_data, component_data)
    ```

    """
    # find mission name
    for candidate_mission_name in missions.keys():
        if design_name in missions[candidate_mission_name]:
            mission_name = candidate_mission_name
    design_data = data_extraction.read_data(design_name)
    req_data = data_extraction.read_data(mission_name)

    # looping through each requirement
    for req, req_text, functional in zip(req_data['Req_ID'], req_data['Requirement'], req_data['Functional_Non_Functional']):
        # if functional, propose new function or link to existing function in design
        if functional == 'Functional_Requirement':
            # print existing functions
            existing_functions =  list_functions(design_data)
            print(f'existing functions:{Fore.GREEN}{existing_functions}{Style.RESET_ALL}')
            response = input(f'add new or existing function for req: {Fore.GREEN}{req}{Style.RESET_ALL} ->{Fore.GREEN}{req_text}{Style.RESET_ALL} (enter number of existing,n for new s for skip)')
            if response != 's':
                if response == 'n':
                    mode_list = list_modes(design_data,mode_data)
                    print(f'modes:{Fore.GREEN}{mode_list}{Style.RESET_ALL}')
                    modes = input('enter modes to assign to (using ids, split using ;, leave empty for none)')
                    modes_string = ';NONE'
                    for mode_id in modes.split(';'):
                        modes_string = modes_string.replace(';NONE','')
                        mode_name = mode_list[int(mode_id)][1]
                        modes_string = modes_string + ';' + mode_name
                    modes_string = modes_string[1:]
                    function_name = 'func-'+str(len(existing_functions))
                    design_data.loc[len(design_data)] = [function_name,'Function', 'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	1,'NONE',	str(req),'NONE',	'NONE',	modes_string,'NONE']
                    design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
                    # update ownership
                    spacecraft_name = identify_spacecraft_name(design_data)
                    add_element_ownership(function_name,spacecraft_name,design_data,design_name)
                else:
                    function_name = existing_functions[int(response)]
                    design_data.loc[design_data['name'] == function_name,'related_requirement'] = design_data.loc[design_data['name'] == function_name,'related_requirement'] + ';' +str(req)
                    design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
                    # update ownership
                    spacecraft_name = identify_spacecraft_name(design_data)
                    add_element_ownership(function_name,spacecraft_name,design_data,design_name)
    
    # now finding modes with no grouped function and generating ones for them
    # identify modes
    mode_list = list_modes(design_data,mode_data)
    mode_assignments_stacked = design_data['grouped_to'].values.tolist()
    mode_assignments_not_flat = []
    for entry in mode_assignments_stacked:
        mode_assignments_not_flat.append(entry.split(';'))
    
    mode_assignments = [
        x
        for xs in mode_assignments_not_flat
        for x in xs
    ]
    for mode in mode_list:
        if mode[1] not in mode_assignments:
            print('adding notional function to mode')
            # add function for this mode
            function_name = 'func-'+str(mode[1])
            design_data.loc[len(design_data)] = [function_name,'Function', 'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	1,'NONE',	'NONE',	'NONE',	'NONE',	'NONE',	mode[1]]
            design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
            spacecraft_name = identify_spacecraft_name(design_data)
            add_element_ownership(function_name,spacecraft_name,design_data,design_name)

def edit_data_file_function_details(label,design_data,function_data,function,design_name,colum_name,append_domain_suffix):
    """
    Edit function details in design and ontology data files.

    Parameters:
    - label (str): The label to update.
    - design_data (DataFrame): DataFrame containing design data.
    - function_data (DataFrame): DataFrame containing function data.
    - function (str): The name of the function to update.
    - design_name (str): The name of the design.
    - column_name (str): The name of the column to update.
    - append_domain_suffix (bool): Whether to append domain suffix.

    Returns:
    None

    This function updates function details in both design and ontology data files based on the provided label.

    It performs the following steps:
    1. Checks if the label is not 'NONE', 'Parameter', and not related to certain elements.
    2. Modifies the label and updates the design and ontology data files accordingly.
    3. Writes the updated design data to the design file.
    4. Writes the updated ontology data to the ontology file.

    Note:
    - The design data and function data are expected to be saved as CSV files.
    - The 'column_name' parameter specifies the column to update in both data files.
    - Both design data and ontology data are expected to be saved in the './data/' directory.

    Example usage:
    ```
    edit_data_file_function_details("LabelA", design_data, function_data, "FunctionX", "DesignA", "ColumnA", True)
    ```

    """
    # now updating design and ontology data files
    if not label == 'NONE' and not label ==  'Parameter' and 'Design_Instance_Element' not in label and 'Valid' not in label and 'compared' not in label:
        if colum_name not in design_data.keys():
            design_data[colum_name] = 'NONE'
        suffix = ''
        # first strip _Domain, then replace with _FDomain
        label = label.replace('_Domain','')
        if '_FDomain' not in label and append_domain_suffix:
            suffix= '_FDomain'
        label = label + suffix
        if label not in design_data.loc[design_data['name'] == function, colum_name].values[0].split(';'):
            design_data.loc[design_data['name'] == function, colum_name] = design_data.loc[design_data['name'] == function, colum_name].replace('NONE','') +';'+ label,
        else:
            print(f'not repeating label: {label} in design')
        print(function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name].values[0])
        print('***')
        print(label)
        print('***')
        if label not in function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name].values[0].split(';'):
            function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name] = function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name].values[0].replace('NONE','') +';'+ label,
        else:
            print(f'not repeating label: {label} in ontology')
    
    # writing to design file
    # if first character is a ';', remove it
    if design_data.loc[design_data['name'] == function, colum_name].values[0][0] == ';':
        design_data.loc[design_data['name'] == function, colum_name] = design_data.loc[design_data['name'] == function, colum_name].values[0][1:]
    design_data.to_csv(f"./data/{design_name}_info.csv", index=False)

    # writing to ontology file
    if function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name].values[0][0] == ';':
        function_data.loc[design_data['name'] == 'Function', 'allowed_'+colum_name] = function_data.loc[function_data['name'] == 'Function', 'allowed_'+colum_name].values[0][1:]
    function_data.to_csv(f"./data/functions_info.csv", index=False)

def add_inferred_assigment_labels(parameter_name,design_data,function_data,function_name,design_name,graph):
    """
    Add inferred assignment labels to related design parameters.

    Parameters:
    - parameter_name (str): The name of the parameter to add inferred assignment labels.
    - design_data (DataFrame): DataFrame containing design data.
    - function_data (DataFrame): DataFrame containing function data.
    - function_name (str): The name of the function.
    - design_name (str): The name of the design.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function identifies parents of the related design parameter and adds inferred assignment labels
    to them based on the provided function name and design data.

    It performs the following steps:
    1. Identifies the parents of the related design parameter.
    2. Loops through the parents until there are no more parents.
    3. Calls the 'edit_data_file_function_details' function to add inferred assignment labels to the parents.
    4. Updates the design and function data files accordingly.

    Note:
    - The design data and function data are expected to be saved as CSV files.
    - The 'parameter_name' parameter specifies the name of the parameter to add inferred assignment labels.
    - The 'graph' parameter should be a Neo4j graph object representing the database.
    - Both design data and ontology data are expected to be saved in the './data/' directory.

    Example usage:
    ```
    add_inferred_assigment_labels("ParameterX", design_data, function_data, "FunctionA", "DesignA", graph)
    ```

    """
    # identify parents of related desing parameter
    parent_flag = True
    root_name = parameter_name
    # loop through parents until no parents
    while parent_flag:
        query = """
                MATCH (root:"""+design_name+"""_Design_Instance_Element {uid:'"""+design_name+root_name+"""'})-[r:PARENT]->(parent:"""+design_name+"""_Design_Instance_Element)
                Return parent
                """
        parent_query = database_tools.run_neo_query(['nil'],query,graph)
        # end when no parents
        if not parent_query:
            parent_flag = False
            break
        parent = parent_query[0]['parent']['name']
        root_name = parent
        edit_data_file_function_details(parent,design_data,function_data,function_name,design_name,'assigned_to',False)

def infer_functional_assignments(design_name,function_data,graph):
    """
    Infer functional assignments and add domain labels based on the loaded design model.

    Parameters:
    - design_name (str): The name of the design.
    - function_data (DataFrame): DataFrame containing function data.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function consults the loaded design model to infer functional assignments and add domain labels.
    It loops through all functions, identifies related modes, components, and requirements, and assigns domains
    as subtypes based on the design model.

    It performs the following steps:
    1. Reads design data from the provided design name.
    2. Constructs a Cypher query to match function, requirement, requirement clause, requirement signal, and design elements.
    3. Runs the query against the Neo4j graph to retrieve function-design element pairs.
    4. Assigns requirement domains, component domains, and adds inferred assignment labels to the design data.

    Note:
    - The design data and function data are expected to be saved as CSV files.
    - The 'graph' parameter should be a Neo4j graph object representing the database.
    - Both design data and ontology data are expected to be saved in the './data/' directory.

    Example usage:
    ```
    infer_functional_assignments("DesignA", function_data, graph)
    ```

    """
    design_data = data_extraction.read_data(design_name)
    # consulting loaded design model to infer functional assignments and add domain labels
    # loop through all functions, identify related modes components,and requirements
    # find requirements and requirement related components and assign domains as subtypes
    query = """
            MATCH (f:Function:"""+design_name+"""_Design_Instance_Element)-[r:SATISFY]-(req:Requirement)-[r4:SATISFY]-(des:"""+design_name+"""_Design_Instance_Element)
            Return f,labels(req) as req_labels,des,labels(des) as des_labels
            """
    function_design_element_pairs = database_tools.run_neo_query(['nil'],query,graph)
    for pair in function_design_element_pairs:
        #assign requirement domains
        for label in pair['req_labels']:
            if '_Domain' in label:
                edit_data_file_function_details(label,design_data,function_data,pair['f']['name'],design_name,'sub_class',True)
        # assign component domains
        for label in pair['des_labels']:
            edit_data_file_function_details(label,design_data,function_data,pair['f']['name'],design_name,'sub_class',True)# add domain tags
        # now adding assignment label
        add_inferred_assigment_labels(pair['des']['name'],design_data,function_data,pair['f']['name'],design_name,graph)
          

    return

def identify_spacecraft_name(design_data):
    """
    Identify the spacecraft name from the provided design data.

    Parameters:
    - design_data (DataFrame): DataFrame containing design data.

    Returns:
    str: The name of the spacecraft.

    This function iterates through the provided design data and identifies the spacecraft name,
    which is associated with the classifier 'Spacecraft'.

    It performs the following steps:
    1. Iterates through each element in the design data.
    2. Checks if the element is classified as 'Spacecraft'.
    3. Returns the name of the spacecraft when found.

    Note:
    - The 'design_data' DataFrame should contain information about design elements.
    - The 'classifier' column is expected to classify elements.

    Example usage:
    ```
    spacecraft_name = identify_spacecraft_name(design_data)
    ```

    """
    for element_name, element_type in zip(design_data['name'], design_data['classifier']):
        if element_type == 'Spacecraft':
            return element_name
    
def add_element_ownership(element_name,parent_name,design_data,design_name):
    """
    Add ownership of an element to a parent element in the design data.

    Parameters:
    - element_name (str): The name of the element to add ownership.
    - parent_name (str): The name of the parent element.
    - design_data (DataFrame): DataFrame containing design data.
    - design_name (str): The name of the design.

    Returns:
    None

    This function adds ownership of an element to a parent element in the design data.
    It updates the 'children' column of the parent element with the name of the owned element.

    It performs the following steps:
    1. Updates the 'children' column of the parent element with the name of the owned element.
    2. Writes the updated design data to the design file.

    Note:
    - The 'design_data' DataFrame should contain information about design elements.
    - Both design data and ontology data are expected to be saved in the './data/' directory.

    Example usage:
    ```
    add_element_ownership("ElementX", "ParentElementY", design_data, "DesignA")
    ```

    """
    design_data.loc[design_data['name'] == parent_name,'children'] = design_data.loc[design_data['name'] == parent_name,'children'] + ';' + element_name
    design_data.to_csv(f"./data/{design_name}_info.csv", index=False)
    
    return


def update_data_file_domains(Domain,data,req,mission_name):
    """
    Update domain information in the data file.

    Parameters:
    - Domain (str): The domain information to update.
    - data (DataFrame): DataFrame containing data.
    - req (str): The requirement ID.
    - mission_name (str): The name of the mission.

    Returns:
    None

    This function updates domain information in the provided data file based on the given domain, requirement ID, and mission name.

    It performs the following steps:
    1. Checks if the provided domain is not 'n'.
    2. Adds a 'domain' column to the data if it does not exist.
    3. Updates the domain information for the specified requirement if the domain is not already present.
    4. Writes the updated data to the mission-specific file.

    Note:
    - The 'data' DataFrame should contain the data to be updated.
    - The 'req' parameter specifies the requirement ID to update.
    - The 'mission_name' parameter specifies the name of the mission.

    Example usage:
    ```
    update_data_file_domains("DomainA", data, "REQ123", "MissionX")
    ```

    """
    print(Domain)
    # now updating data file
    if not Domain == 'n':
        if 'domain' not in data.columns:
            data=data.assign(domain='NONE')
        if Domain not in str(data.loc[data['Req_ID'] == req, 'domain']):
            print(req,Domain)
            print('***')
            print(data['domain'])
            print('***')
            print(data.loc[data['Req_ID'] == req, 'domain'].values[0])
            data.loc[data['Req_ID'] == req, 'domain'] = data.loc[data['Req_ID'] == req, 'domain'].values[0].replace('NONE','') + ';'+ Domain,
        else:
            print(f'not repeating label: {Domain}')
    data.to_csv(f"./data/{mission_name}_info.csv", index=False)
    
def update_data_file_with_label(label,data,req,mission_name,colum_name):
    """
    Update data file with the given label.

    Parameters:
    - label (str): The label to update.
    - data (list): A list containing DataFrames representing different sheets of the Excel file.
    - req (str): The requirement ID.
    - mission_name (str): The name of the mission.
    - colum_name (str): The name of the column to update.

    Returns:
    None

    This function updates the provided data file with the given label for the specified requirement.

    It performs the following steps:
    1. Checks if the provided label is not 'n'.
    2. Adds a new column with the given name if it does not exist in the first sheet.
    3. Updates the label for the specified requirement if it is not already present.
    4. Writes the updated data to the mission-specific Excel file with multiple sheets.

    Note:
    - The 'data' list should contain DataFrames representing different sheets of the Excel file.
    - The 'req' parameter specifies the requirement ID to update.
    - The 'mission_name' parameter specifies the name of the mission.
    - The 'colum_name' parameter specifies the name of the column to update.

    Example usage:
    ```
    update_data_file_with_label("LabelA", data, "REQ123", "MissionX", "ColumnA")
    ```

    """
    # now updating data file
    #if colum_name not in data.columns:
    #    data=data.assign(colum_name='NONE')
    if not label == 'n':
        if colum_name not in data[0].keys():
            data[0][colum_name] = 'NONE'
        if label not in str(data[0].loc[data[0]['Req ID'] == req, colum_name]):
            data[0].loc[data[0]['Req ID'] == req, colum_name] = data[0].loc[data[0]['Req ID'] == req, colum_name].replace('NONE','') + label,
        else:
            print(f'not repeating label: {label}')
        # Write to Multiple Sheets
    with pd.ExcelWriter(f"./data/{mission_name}_Parsed_Requirement_info.xlsx") as writer:
        data[0].to_excel(writer,sheet_name = 'Requirements-Output', index=False)
        data[1].to_excel(writer,sheet_name = 'Step-By-Step', index=False)


def edit_mission_functional_requirements(mission_name,missions,graph):
    """
    Edit functional requirements of a mission.

    Parameters:
    - mission_name (str): The name of the mission.
    - missions (dict): A dictionary mapping mission names to their associated designs.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function allows for the editing of functional requirements of a mission.
    It reads mission data from a file and iterates through each requirement,
    prompting the user to label it as functional or non-functional.

    It performs the following steps:
    1. Reads mission data from the provided mission name.
    2. Iterates through each requirement and prompts the user to label it as functional or non-functional.
    3. Updates the database with the functional label for each requirement.
    4. Updates the data file with the corresponding functional/non-functional label.

    Note:
    - The mission data is expected to be saved in a file named '{mission_name}_info.csv'.
    - The 'missions' dictionary should contain mappings of mission names to associated designs.
    - The 'graph' parameter should be a Neo4j graph object representing the database.

    Example usage:
    ```
    edit_mission_functional_requirements("MissionA", missions, graph)
    ```

    """
    data = data_extraction.read_data(mission_name)
    # ASSUMING DATA ALREADY LOADED IN DATABASE
    req_data = data
    print(req_data)
    for req, req_text in zip(req_data['Req_ID'], req_data['Requirement']):
        # asking user for suggested functional label
        user_response = input(f'is requirement {Fore.GREEN}{req}{Style.RESET_ALL} -> {Fore.GREEN}{req_text}{Style.RESET_ALL} functional? (n/y, s to skip)')
        if user_response == 'y':
            functional_label = 'Functional_Requirement'
            print('labelling requirement as functional')
            query = """
                MATCH (n:Requirement {uid:'"""+mission_name+str(req)+"""'})
                    SET n:"""+functional_label+"""
                """
            database_tools.run_neo_query(['nil'],query,graph)
            # now updating data file
            update_data_file_with_label(functional_label,data,req,mission_name,'Functional Non Functional')

        elif user_response == 'n':
            functional_label = 'Non_Functional_Requirement'
            print('labelling requirement as non functional')
            query = """
                MATCH (n:Requirement {uid:'"""+mission_name+str(req)+"""'})
                    SET n:"""+functional_label+"""
                """
            database_tools.run_neo_query(['nil'],query,graph)
            # now updating data file
            update_data_file_with_label(functional_label,data,req,mission_name,'Functional Non Functional')

def edit_mission_domains(mission_name,graph):
    """
    Edit domains of requirements for a mission.

    Parameters:
    - mission_name (str): The name of the mission.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function allows for the editing of domains of requirements for a mission.
    It reads mission data from a file and iterates through each requirement,
    prompting the user to suggest domain labels.

    It performs the following steps:
    1. Reads mission data from the provided mission name.
    2. Iterates through each requirement and prompts the user to suggest domain labels.
    3. Updates the database with the suggested domain labels for each requirement.
    4. Updates the data file with the corresponding domain labels.

    Note:
    - The mission data is expected to be saved in a file named '{mission_name}_Info.csv'.
    - The 'graph' parameter should be a Neo4j graph object representing the database.

    Example usage:
    ```
    edit_mission_domains("MissionA", graph)
    ```

    """
    data = pd.read_csv('data/'+mission_name+'_Info.csv')
    
    # ASSUMING DATA ALREADY LOADED IN DATABASE
    req_data = data
    for  req, req_text in zip(req_data['Req_ID'], req_data['Requirement']):
        # asking user for suggested domain label
        user_suggested_Domain = input(f'Please suggest requirement domain for:{Fore.GREEN}{req}: {req_text}{Style.RESET_ALL} (n to avoid, use ; to separate multiple domains, include _Domain at the end)')
        print('tagging in data base (wont work with multiple, only after reload)')
        query = """
            MATCH (n:Requirement {uid:'"""+mission_name+str(req)+"""'})
                SET n:"""+user_suggested_Domain+"""
            """
        database_tools.run_neo_query(['nil'],query,graph)

        # now updating data file
        update_data_file_domains(user_suggested_Domain,data,req,mission_name)

        # finding related design element classifiers and labelling this as domain
        query = """
        MATCH (n:Requirement {uid:'"""+mission_name+str(req)+"""'})-[r:SATISFY]-(n2:Design_Element)
        RETURN n2.Classifier
        """
        response = database_tools.run_neo_query(['nil'],query,graph)
        for entry in response:
            related_classifier_label = entry['n2.Classifier']+'_Domain'
            query = """
            MATCH (n:Requirement {uid:'"""+mission_name+str(req)+"""'})
            SET n:"""+related_classifier_label+"""
            """
            response = database_tools.run_neo_query(['nil'],query,graph)

            print(response)
            update_data_file_domains(related_classifier_label,data,req,mission_name)

def list_domain_labels(mission_name):
    """
    List domain labels for a mission.

    Parameters:
    - mission_name (str): The name of the mission.

    Returns:
    None

    This function lists domain labels for a given mission.
    It reads mission data from an Excel file and extracts domain labels from the 'domain' column.

    It performs the following steps:
    1. Reads mission data from the provided mission name.
    2. Iterates through each row and splits domain labels separated by ';'.
    3. Appends unique domain labels to the 'domains' list.
    4. Prints the list of domain labels.

    Note:
    - The mission data is expected to be saved in an Excel file named '{mission_name}_Parsed_Requirement_Info.xlsx'.

    Example usage:
    ```
    list_domain_labels("MissionA")
    ```

    """
    data = pd.read_csv('data/'+mission_name+'_Info.csv')
    domains = []
    for row in data['domain']:
        for domain in row.split(';'):
            if domain not in domains and domain != 'NONE':
                domains.append(domain)
    #print(f'{Fore.GREEN}printing domains{Style.RESET_ALL}')
    for domain in domains:
        pass#print(f"'{domain}',")
    #print(f'{Fore.GREEN}***{Style.RESET_ALL}')
    return domains

def list_sub_class_labels(design_name):
    """
    List sub-class labels for a design.

    Parameters:
    - design_name (str): The name of the design.

    Returns:
    None

    This function lists sub-class labels for a given design.
    It reads design data from a file and extracts sub-class labels from the 'sub_class' column.

    It performs the following steps:
    1. Reads design data from the provided design name.
    2. Iterates through each row and splits sub-class labels separated by ';'.
    3. Appends unique sub-class labels to the 'sub_classes' list.
    4. Prints the list of sub-class labels.

    Note:
    - The design data is expected to be saved in a file named '{design_name}_info.csv'.

    Example usage:
    ```
    list_sub_class_labels("DesignA")
    ```

    """
    data = data_extraction.read_data(design_name)
    sub_classes = []
    for row in data['sub_class']:
        for sub_class in row.split(';'):
            if sub_class not in sub_classes and sub_class != 'NONE':
                #print(sub_class)
                sub_classes.append(sub_class)
    #print(f'{Fore.GREEN}printing sub_classes:{Style.RESET_ALL}')
    for sub_class in sub_classes:
        pass#print(f"'{sub_class}',")
    #print(f'{Fore.GREEN}***{Style.RESET_ALL}')

    return sub_classes

def list_classifiers_of_type(classifier_data):
    classifiers = []
    for row in classifier_data['name']:
        for classifier in row.split(';'):
            if classifier not in classifiers and classifier != 'NONE':
                #print(sub_class)
                classifiers.append(classifier)
    #print(f'{Fore.GREEN}printing sub_classes:{Style.RESET_ALL}')
    for classifier in classifiers:
        pass#print(f"'{sub_class}',")
    #print(f'{Fore.GREEN}***{Style.RESET_ALL}')

    return classifiers

def list_design_elements(design_data):
    element_list = []
    for element, element_classifier in zip(design_data['name'], design_data['classifier']):
        element_list.append([len(element_list),element,element_classifier])
    return element_list

def refresh_model_in_data_based(design_name,design_data,mission_name,graph):
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

    pyDRAGONS.database_interaction.data_extraction.load_mission_requirements(mission_name,graph)

    pyDRAGONS.database_interaction.data_extraction.process_design_data(mission_name,design_name,design_data,graph)
