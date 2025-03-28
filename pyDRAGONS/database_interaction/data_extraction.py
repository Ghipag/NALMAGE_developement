import pandas as pd
from . import  database_tools
from . import ontology_checking

def read_data(name):
    """
    Read data from a CSV file and return it as a DataFrame.

    This function reads a CSV file located in the './data/' directory with the
    given 'name' and returns its contents as a pandas DataFrame.

    @param name: The name of the CSV file (excluding the '.csv' extension).
    @type name: str

    @return: A pandas DataFrame containing the data from the CSV file.
    @rtype: pandas.DataFrame

    @pre The CSV file must exist in the './data/' directory.
    @post The returned DataFrame will contain the data from the CSV file.

    @warning If the specified CSV file does not exist, this function will raise
             a FileNotFoundError.

    @see: You can use the pandas library for further data manipulation and analysis.
    """
    data = pd.read_csv(

        f"./data/{name}_Info.csv",
        low_memory=False)
    #print("Column name of data : ", data.columns)
    return data

def generate_uid(data,type_tag):
    """
    Generate unique identifiers (UIDs) and add them as a new column in a DataFrame.

    This function takes a pandas DataFrame 'data' and a 'type_tag' as input. It generates
    unique identifiers by combining the 'type_tag' and the 'name' column values (or others for 
    requirements and requirement clauses) for each row in the DataFrame. The UIDs are added 
    as a new 'uid' column in the DataFrame.

    @param data: The input DataFrame containing at least a 'name' column.
    @type data: pandas.DataFrame

    @param type_tag: A string used as a prefix to create unique identifiers.
    @type type_tag: str

    @return: The input DataFrame with an additional 'uid' column containing the generated UIDs.
    @rtype: pandas.DataFrame

    @pre The 'data' DataFrame must contain a 'name' column.
    @post The returned DataFrame will have an additional 'uid' column with unique identifiers.

    @warning If the 'name' column does not exist in the input DataFrame, this function will raise
             a KeyError.

    @see: You can use the pandas library for further DataFrame manipulation and analysis.
    """
    #add uid colum as CUSTOMTAG / element name
    uids =  []
    traceable_to_list = []
    rating_list = []
    #print(data.keys())
    for index, row in data.iterrows():
        uids.append(type_tag + str(row['name']))
        if 'traceable_to' in row.keys():
            traceable_to_list.append(str(row['traceable_to']))
        else:
            traceable_to_list.append('NONE')
        if 'rating' in row.keys():
            rating_list.append(str(row['rating']))
        else:
            rating_list.append('NONE')

    # add to original data frame
    data['uid'] = uids
    data['traceable_to'] = traceable_to_list
    data['rating'] = rating_list
    return data

def process_function_classifier_data(data,graph):
    """
    Process and insert function classifier data into a Neo4j graph database.

    This function takes function classifier data in the form of a pandas DataFrame 'data'
    and inserts it into a Neo4j graph database specified by the 'graph' parameter. The function
    performs several data processing steps, including generating unique identifiers, filtering,
    and formatting the data, and creating nodes and relationships in the graph.

    @param data: The input DataFrame containing function classifier data.
    @type data: pandas.DataFrame

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The function classifier data is inserted into the Neo4j graph database.

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    
    data = generate_uid(data,'ontology/')

    input_data = data[['uid','name','alternative_names', 'allowed_owner', 'allowed_sub_class',]]
    #drop empty entries
    input_data =  input_data.dropna()


    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())
    query = """
            UNWIND $rows AS row

            MERGE (function:Function_Classifier {uid:row.uid})
            SET 
                function:Classifier,
                function.name = row.name,
                function.Alternative_Names = row.alternative_names,
                function.Allowed_Owner = row.allowed_owner
        """
    database_tools.run_neo_query(input_data,query,graph)

    
def process_component_classifier_data(data,graph):
    """
    Process and insert component classifier data into a Neo4j graph database.

    This function takes component classifier data in the form of a pandas DataFrame 'data'
    and inserts it into a Neo4j graph database specified by the 'graph' parameter. The function
    performs several data processing steps, including generating unique identifiers, filtering,
    and formatting the data, and creating nodes and relationships in the graph.

    @param data: The input DataFrame containing component classifier data.
    @type data: pandas.DataFrame

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The component classifier data is inserted into the Neo4j graph database.

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    
    data = generate_uid(data,'ontology/')

    input_data = data[['uid','name','alternative_names', 'allowed_owner', 'allowed_component_levels','allowed_sub_class', 'allowed_allocated_function_types', 'allowed_power_interfaces', 'allowed_data_interfaces', 'allowed_mechanical_interfaces', 'allowed_fluid_interfaces','allowed_thermal_interfaces']]
    #drop empty entries
    input_data =  input_data.dropna()


    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())
    query = """
            UNWIND $rows AS row

            MERGE (component:Component_Classifier {uid:row.uid})
            SET 
                component:Classifier,
                component.name = row.name,
                component.Alternative_Names = row.alternative_names,
                component.Allowed_Owner = row.allowed_owner,
                component.Allowed_Component_Levels = row.allowed_component_levels,
                component.Allocated_Functions = row.allocated_functions,
                component.Allowed_Allocated_function_types = row.allowed_allocated_function_types,
                component.Modes = row.modes
        """
    database_tools.run_neo_query(input_data,query,graph)
    # update labels for component level
    query = """ 
            MATCH(component:Component_Classifier {Allowed_Component_Levels:'Root'})
            WITH component
            SET component:Root_Classifier
            """
    database_tools.run_neo_query(input_data,query,graph)

    query = """ 
            MATCH(component:Component_Classifier {Allowed_Component_Levels:'Subsystem'})
            WITH component
            SET component:Subsystem_Classifier
            """
    database_tools.run_neo_query(input_data,query,graph)

    query = """ 
            MATCH(component:Component_Classifier {Allowed_Component_Levels:'Unit'})
            WITH component
            SET component:Unit_Classifier
        """

    database_tools.run_neo_query(input_data,query,graph)


    # adding relationships to allowed owners
    database_tools.process_relationships(data,'Component_Classifier','allowed_owner','Component_Classifier','ALLOWED_OWNER','OUTGOING',graph)

    # adding relationships for power allowed interfaces
    database_tools.process_relationships(data,'Component_Classifier','allowed_power_interfaces','Component_Classifier','ALLOWED_POWER_INTERFACE','BOTH',graph)

    # adding relationships for data allowed interfaces
    database_tools.process_relationships(data,'Component_Classifier','allowed_data_interfaces','Component_Classifier','ALLOWED_DATA_INTERFACE','BOTH',graph)

    # adding relationships for mechanical allowed interfaces
    database_tools.process_relationships(data,'Component_Classifier','allowed_mechanical_interfaces','Component_Classifier','ALLOWED_MECHANICAL_INTERFACE','BOTH',graph)

    # adding relationships for fluid allowed interfaces
    database_tools.process_relationships(data,'Component_Classifier','allowed_fluid_interfaces','Component_Classifier','ALLOWED_FLUID_INTERFACE','BOTH',graph)

    # adding relationships for thermal allowed interfaces
    database_tools.process_relationships(data,'Component_Classifier','allowed_thermal_interfaces','Component_Classifier','ALLOWED_THERMAL_INTERFACE','BOTH',graph)

def process_condition_classifier_data(data,graph):
    """
    Process and insert condition classifier data into a Neo4j graph database.

    This function takes condition classifier data in the form of a pandas DataFrame 'data'
    and inserts it into a Neo4j graph database specified by the 'graph' parameter. The function
    performs several data processing steps, including generating unique identifiers, filtering,
    and formatting the data, and creating nodes in the graph.

    @param data: The input DataFrame containing condition classifier data.
    @type data: pandas.DataFrame

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The condition classifier data is inserted into the Neo4j graph database.

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    data = generate_uid(data,'ontology/')
    input_data = data[['uid','name','alternative_names', 'reciprocal', 'allowed_sub_class']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (condition:Condition_Classifier {uid:row.name})
            SET 
                condition:Classifier,
                condition.name = row.name,
                condition.Alternative_Names = row.alternative_names,
                condition.Reciprocal = row.reciprocal,
                condition.allowed_sub_class = row.allowed_sub_class
                
        """
    database_tools.run_neo_query(input_data,query,graph)


def process_mode_classifier_data(data,graph):
    """
    Process and insert mode classifier data into a Neo4j graph database.

    This function takes mode classifier data in the form of a pandas DataFrame 'data'
    and inserts it into a Neo4j graph database specified by the 'graph' parameter. The function
    performs several data processing steps, including generating unique identifiers, filtering,
    and formatting the data, and creating nodes and relationships in the graph.

    @param data: The input DataFrame containing mode classifier data.
    @type data: pandas.DataFrame

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The mode classifier data is inserted into the Neo4j graph database with relationships to allowed owners and conditions.

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    data = generate_uid(data,'ontology/')
    input_data = data[['uid','name','alternative_names', 'allowed_owner', 'allowed_sub_class','allowed_conditions']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (mode:Mode_Classifier {uid:row.uid})
            SET 
                mode:Classifier,
                mode.name = row.name,
                mode.Alternative_Names = row.alternative_names,
                mode.Allowed_Owner = row.allowed_owner,
                mode.allowed_sub_class = row.allowed_sub_class,
                mode.Allowed_Conditions = row.allowed_conditions
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # adding relationships to allowed owners
    database_tools.process_relationships(data,'Mode_Classifier','allowed_owner','Component_Classifier','ALLOWED_OWNER','OUTGOING',graph)

    # adding relationships for allowed conditions
    database_tools.process_relationships(data,'Mode_Classifier','allowed_conditions','Condition_Classifier','ALLOWED_CONDITION','OUTGOING',graph)

def process_parameter_classifier_data(data,graph):
    """
    Process and insert parameter classifier data into a Neo4j graph database.

    This function takes parameter classifier data in the form of a pandas DataFrame 'data'
    and inserts it into a Neo4j graph database specified by the 'graph' parameter. The function
    performs several data processing steps, including generating unique identifiers, filtering,
    and formatting the data, and creating nodes and relationships in the graph.

    @param data: The input DataFrame containing parameter classifier data.
    @type data: pandas.DataFrame

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The parameter classifier data is inserted into the Neo4j graph database with relationships to owners (Components, Subsystems, and Units).

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    data = generate_uid(data,'ontology/')
    input_data = data[['uid','name','alternative_names', 'allowed_owner', 'allowed_sub_class','allowed_type','allowed_categories','units']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (parameter:Parameter_Classifier {uid:row.uid})
            SET 
                parameter:Classifier,
                parameter.name = row.name,
                parameter.Alternative_Names = row.alternative_names,
                parameter.Allowed_Owner = row.allowed_owner,
                parameter.allowed_sub_class = row.allowed_sub_class,
                parameter.Allowed_Type = row.allowed_type,
                parameter.Allowed_Conditions = row.allowed_categories,
                parameter.Units = row.units
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # adding relationships for parent components
    # firstly removing relations to general Subsystem and Unit owners for special handling later
    indexes = []
    for index, row in data.iterrows():
        for owner in row['allowed_owner'].split(';'):
            if 'Subsystem' == owner:
                indexes.append(index)
            if 'Unit' == owner:
                indexes.append(index)
    selected_data = data.drop(indexes)

    database_tools.process_relationships(selected_data,'Parameter_Classifier','allowed_owner','Component_Classifier','ALLOWED_OWNER','OUTGOING',graph) 

    # now adding relationships to general Subsystems and Units
    # Subsystems
    indexes = []
    for index, row in data.iterrows():
        for owner in row['allowed_owner'].split(';'):
            if 'Subsystem' == owner:
                indexes.append(index)
    selected_data = data.loc[indexes]
    database_tools.process_relationships_to_generic(selected_data,'Parameter_Classifier','allowed_owner','Subsystem_Classifier','ALLOWED_OWNER','OUTGOING',graph) 

    # Units
    indexes = []
    for index, row in data.iterrows():
        for owner in row['allowed_owner'].split(';'):
            if 'Unit' == owner:
                indexes.append(index)
    selected_data = data.loc[indexes]
    database_tools.process_relationships_to_generic(selected_data,'Parameter_Classifier','allowed_owner','Unit_Classifier','ALLOWED_OWNER','OUTGOING',graph) 

def process_design_data(mission_name,design_name,data,ontology_graph):
    """
    Process and insert design data into a Neo4j graph database.

    This function takes design data, represented as a pandas DataFrame 'data', and inserts it into a Neo4j
    graph database specified by the 'ontology_graph' parameter. The function performs several data processing
    steps, including generating unique identifiers, filtering, and formatting the data, and creating nodes and
    relationships in the graph to represent design elements and their properties.

    @param design_name: The name or identifier for the specific design instance being processed.
    @type design_name: str

    @param data: The input DataFrame containing design data.
    @type data: pandas.DataFrame

    @param ontology_graph: The Neo4j graph database connection for ontology data.
    @type ontology_graph: neo4j.Graph

    @pre The 'data' DataFrame must conform to a specific structure with defined columns.
    @post The design data is inserted into the Neo4j graph database with relationships to classifiers, children, and interfaces.

    @warning This function assumes a specific data structure and may not work with arbitrary dataframes.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    data = generate_uid(data,design_name)
    input_data = data[['uid','name','classifier','children','power_interfaces','data_interfaces','mechanical_interfaces','fluid_interfaces','parameter_value','multiplicity','sub_class']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())
    for row in input_data:
        # need to check for multiple sub classes
        subclass = row['sub_class']
        if ';' in row['sub_class']:
            subclass = row['sub_class'].split(';')
        subclass_str = ''
        if isinstance(subclass, list):
            for sub in subclass:
                subclass_str = subclass_str + ':' + sub 
            subclass_str = subclass_str[1:] # remove first :
        else:
            subclass_str = subclass
        

        #element:"""+ subclass_str +""", # for adding subclass labels
        query = """
                MERGE (element:"""+design_name+"""_Design_Instance_Element {uid: '"""+ row['uid'] +"""'})
                SET 
                    element:Design_Element,
                    element:"""+ row['classifier'] +""",
                    element:"""+ subclass_str +""",
                    element.name = '"""+ row['name'] +"""',
                    element.Classifier = '"""+ row['classifier'] +"""',
                    element.Sub_Class = '"""+ subclass_str +"""',
                    element.Multiplicity = """+ str(row['multiplicity']) +"""
            """
        ontology_checking.run_valid_neo_query(input_data,query,ontology_graph)

    # now adding relationships for classifiers
    database_tools.process_relationships(data,design_name+'_Design_Instance_Element','classifier','Classifier','CLASSIFIER','OUTGOING',ontology_graph)

    # inherit  labels from each classifier and assign related properties
    for row in input_data:
        query = """
                MATCH (target:"""+design_name+"""_Design_Instance_Element {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(target_classifier)
                WHERE target_classifier:Subsystem_Classifier
                SET target:Subsystem
                """
        database_tools.run_neo_query([row],query,ontology_graph)
        query = """
                MATCH (target {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(target_classifier)
                WHERE target_classifier:Unit_Classifier
                SET target:Unit
                """
        database_tools.run_neo_query([row],query,ontology_graph)
        query = """
                MATCH (target {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(target_classifier)
                WHERE target_classifier:Mode_Classifier
                SET target:Mode
                """
        database_tools.run_neo_query([row],query,ontology_graph)
        if row['parameter_value'] == 'NONE':
            parameter_value = "'NONE'"
        else:
            parameter_value = row['parameter_value']
        query = """
                MATCH (target:"""+design_name+"""_Design_Instance_Element {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(target_classifier)
                WHERE target_classifier:Parameter_Classifier
                SET target:Parameter, target.Value = """+parameter_value+""", target.Units = target_classifier.Units
                """
        database_tools.run_neo_query([row],query,ontology_graph)

    # now adding relationships for children
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','children',design_name+'_Design_Instance_Element','PARENT','ALLOWED_OWNER','OUTGOING',ontology_graph)

    # now adding relationships for power interfaces
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','power_interfaces',design_name+'_Design_Instance_Element','POWER_INTERFACE','ALLOWED_POWER_INTERFACE','BOTH',ontology_graph)

    # now adding relationships for data interfaces
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','data_interfaces',design_name+'_Design_Instance_Element','DATA_INTERFACE','ALLOWED_DATA_INTERFACE','BOTH',ontology_graph)

    # now adding relationships for mechanical interfaces
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','mechanical_interfaces',design_name+'_Design_Instance_Element','MECHANICAL_INTERFACE','ALLOWED_MECHANICAL_INTERFACE','BOTH',ontology_graph)

    # now adding relationships for fluid interfaces
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','fluid_interfaces',design_name+'_Design_Instance_Element','FLUID_INTERFACE','ALLOWED_FLUID_INTERFACE','BOTH',ontology_graph)

    # now adding relationships for thermal interfaces
    ontology_checking.process_valid_relationships(data,design_name+'_Design_Instance_Element','thermal_interfaces',design_name+'_Design_Instance_Element','THERMAL_INTERFACE','ALLOWED_THERMAL_INTERFACE','BOTH',ontology_graph)

    # now adding relationships for active components for each mode
    database_tools.process_relationships(data,design_name+'_Design_Instance_Element','active_components',design_name+'_Design_Instance_Element','ACTIVE_COMPONENT','OUTGOING',ontology_graph)

    # now adding assigned to relationships for related components for each function
    database_tools.process_relationships(data,design_name+'_Design_Instance_Element','assigned_to',design_name+'_Design_Instance_Element','ASSIGNED_TO','OUTGOING',ontology_graph)

    # now adding grouped to relationships for related modes for each function
    database_tools.process_relationships(data,design_name+'_Design_Instance_Element','grouped_to',design_name+'_Design_Instance_Element','GROUPED_TO','OUTGOING',ontology_graph)

    # now adding grouped to relationships for dependant parameters for each function
    # NOTE hard dependency is defined here as a design element value that depends on the value or aspect another design element, only direct dependencies are recorded
    # indirect dependency can be inferred by traversing to neighbors of direct dependant via any (in design) relationship -> allowing any design element to 
    # eventually be traced back to a requirement. traceability can be ranked as a design elements  shortest path to a requirement. The relationship is intended also 
    # as a proxy for analysis driving the values of certain design elements. in leu of the actual dependant parameter existing in the model, the owning design element
    # is recorded
    database_tools.process_relationships(data,design_name+'_Design_Instance_Element','hard_dependency',design_name+'_Design_Instance_Element','HARD_DEPENDENCY','OUTGOING',ontology_graph)

    # now adding relationships for satisfying requirements
    process_satisfy_relationships(data,design_name,mission_name,ontology_graph)

def process_satisfy_relationships(data,design_name,mission_name,graph):
    """
    Process satisfy relationships between design components and mission requirements.

    Parameters:
    - data (DataFrame): The data containing relationships between design components and requirements.
    - design_name (str): The name of the design.
    - mission_name (str): The name of the mission.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function establishes direct 'satisfy' relationships between design components
    and mission requirements in the Neo4j graph database.

    It performs the following steps:
    1. Defines the source and target node types for the relationship.
    2. Specifies the key in the 'data' DataFrame containing requirement information.
    3. Sets the relationship name to 'SATISFY'.
    4. Calls a utility function to process the relationships and add them to the graph.

    Note:
    - The 'data' DataFrame is expected to contain the necessary information
      to establish the satisfy relationships.
    - The 'graph' parameter should be a Neo4j graph object representing the database.

    Example usage:
    ```
    data = pd.DataFrame(...)  # Data containing relationship information
    process_satisfy_relationships(data, "DesignA", "MissionX", graph)
    ```

    """
    # add direct satisfy relationships with functions components
    sourceType = design_name+'_Design_Instance_Element'
    targetType = mission_name+'_Requirement_Element'
    targetKey = 'related_requirement'
    relationshipName = 'SATISFY'

    database_tools.process_relationships(data,sourceType,targetKey,targetType,relationshipName,'OUTGOING',graph)

def load_mission_requirements(mission_name,graph):
    """
    Load mission requirements into a Neo4j graph database.

    Parameters:
    - mission_name (str): The name of the mission.
    - graph: The Neo4j graph object to which the requirements will be loaded.

    Returns:
    None

    This function reads mission requirements data from a file, processes it,
    and loads it into the Neo4j graph database specified by the 'graph' parameter.

    It performs the following steps:
    1. Reads data from a file using the 'mission_name'.
    2. Generates unique identifiers for the requirements.
    3. Converts the data to a list of dictionaries for bulk insertion.
    4. Executes a Cypher query to merge requirement nodes into the graph.
    5. Adds domain labels to requirement nodes if domain information is provided.

    Note:
    - The function expects the 'graph' parameter to be a Neo4j graph object.
    - The format of the mission requirements data file should be compatible
      with the processing steps defined in this function.

    Example usage:
    ```
    graph = neo4j.GraphDatabase.driver("bolt://localhost:7687")
    load_mission_requirements("MissionX", graph)
    ```

    """
    # first loading requirement nodes
    data = read_data(mission_name)

    data['name'] =  data['Req_ID']
    data = generate_uid(data,mission_name)

    input_data = data[['uid','Req_ID','Requirement','Functional_Non_Functional']]

    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (requirement:Requirement {uid:row.uid})
            SET 
                requirement:"""+mission_name+"""_Requirement_Element,
                requirement.name = row.Req_ID,
                requirement.uid = row.uid,
                requirement.Text = row.Requirement,
                requirement.Functional_Non_Functional = row.Functional_Non_Functional
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # if domains have correct labels, now add these labels
    if 'domain' in list(data.columns):
        # process domains
        input_data = data[['uid','domain']]
        
        #drop empty entries
        input_data =  input_data.dropna()

        # Convert data frame to list of dictionaries
        # Neo4j UNWIND query expects a list of dictionaries
        # for bulk insertion
        input_data = list(input_data.T.to_dict().values())
            
        # specifically adding domains for each requirement element
        for row in input_data:
            for domain in row['domain'].split(';'):
                query = """
                        MATCH (n:Requirement {uid:'"""+row['uid']+"""'})
                        SET n:"""+domain+"""
                                    
                    """
                database_tools.run_neo_query(input_data,query,graph)

def load_complex_mission_requirements(mission_name,graph):
    """
    NOTE: NO LONGER USED
    """
    # first loading requirement parameters and signals information 
    data = pd.read_excel('data/'+mission_name+'_Requirement_Info.xlsx',sheet_name=[1,2])

    sig_data = data[1]
    para_data = data[2]
    # need to rename columns to remove spaces
    #signals sheet
    for col in sig_data.columns:
        if col == 'Signal Name':
            sig_data.rename(columns={col:'name'},inplace=True)
        else:
            sig_data.rename(columns={col:col.replace(' ','_')},inplace=True)
    #parameters sheet
    for col in para_data.columns:
        if col == 'Parameter Name':
            para_data.rename(columns={col:'name'},inplace=True)
        else:
            para_data.rename(columns={col:col.replace(' ','_')},inplace=True)
    
    sig_data = generate_uid(sig_data,mission_name)
    para_data = generate_uid(para_data,mission_name)

    # process signals
    input_data = sig_data[['uid','name','Data_type', 'Signal_Desc']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (signal:Requirement_Signal {uid:row.uid})
            SET 
                signal:"""+mission_name+"""_Requirement_Element,
                signal.uid = row.uid,
                signal.name = row.name,
                signal.Data_type = row.Data_type,
                signal.Signal_Desc = row.Signal_Desc
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # process requriement parameters
    input_data = para_data[['uid','name','Data_Type','Value', 'Parameter_Description']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (parameter:Requirement_Parameter {uid:row.uid})
            SET 
                parameter:"""+mission_name+"""_Requirement_Element,
                parameter.uid = row.uid,
                parameter.name = row.name,
                parameter.Data_type = row.Data_type,
                parameter.Value = row.Value,
                parameter.Parameter_Description = row.Parameter_Description
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # now loading clause information
    data = pd.read_excel('data/'+mission_name+'_Parsed_Requirement_Info.xlsx',sheet_name=[0,1])

    req_data = data[0]
    clause_data = data[1]
    # need to rename columns to remove spaces
    #requirements sheet
    for col in req_data.columns:
        if col == 'Req ID':
            req_data.rename(columns={col:'name'},inplace=True)
        else:
            req_data.rename(columns={col:col.replace(' ','_')},inplace=True)
    #clauses sheet
    for col in clause_data.columns:
        clause_data.rename(columns={col:col.replace(' ','_')},inplace=True)
    
    # adding clause name column as simply indexes
    clause_data['name'] = clause_data.index

    # assign uids
    req_data = generate_uid(data[0],mission_name)
    clause_data = generate_uid(data[1],mission_name)
     
    # process requirements
    input_data = req_data[['uid','name','Req_Desc', 'Generated_Output']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())

    query = """
            UNWIND $rows AS row

            MERGE (requirement:Requirement {uid:row.uid})
            SET 
                requirement:"""+mission_name+"""_Requirement_Element,
                requirement.uid = row.uid,
                requirement.Req_Desc = row.Req_Desc,
                requirement.Modelled_Condition = row.Generated_Output
                
        """
    database_tools.run_neo_query(input_data,query,graph)

    # need to add each name as a string (even though appears as a number) individually
    for row in input_data:
        query = """
   
                MERGE (requirement:Requirement {uid: '"""+ row['uid'] +"""'})
                SET 
                    requirement.name ='"""+ str(row['name']) +"""'

                    
            """
        database_tools.run_neo_query(input_data,query,graph)

    # process clauses
    input_data = clause_data[['uid','Req_ID','Clause', 'Signal_Name','Comparison_Symbol','Parameter']]
    
    #drop empty entries
    input_data =  input_data.dropna()

    # Convert data frame to list of dictionaries
    # Neo4j UNWIND query expects a list of dictionaries
    # for bulk insertion
    input_data = list(input_data.T.to_dict().values())
    query = """
            UNWIND $rows AS row
            
            MERGE (clause:Requirement_Clause {uid:row.uid})
            SET 
                clause:"""+mission_name+"""_Requirement_Element,
                clause.Comparison_Symbol = row.Comparison_Symbol,
                clause.Clause = row.Clause,
                clause.Signal_Name = row.Signal_Name,
                clause.Parameter = row.Parameter,
                clause.ReqID =row.Req_ID
            """
    database_tools.run_neo_query(input_data,query,graph)
    
    # specifically adding types for comparison symbol
    for row in input_data:
        Comparison_Symbol_proxy = row['Comparison_Symbol']
        if row['Comparison_Symbol'] == "'=":
            Comparison_Symbol_proxy = "equal"
        elif row['Comparison_Symbol'] == ">":
            Comparison_Symbol_proxy = "more_than"
        elif row['Comparison_Symbol'] == "<":
            Comparison_Symbol_proxy = "less_than"
        query = """
                MERGE (clause:Requirement_Clause {uid: '"""+ row['uid'] +"""'})
                SET 
                    clause:"""+Comparison_Symbol_proxy+"""
                    
            """
        database_tools.run_neo_query(input_data,query,graph)

    # adding relationships to parent requirements
    database_tools.process_relationships(clause_data,'Requirement_Clause','Req_ID','Requirement','PARENT_REQUIREMENT','OUTGOING',graph)
    
    # adding relationships to requirement parameters
    database_tools.process_relationships(clause_data,'Requirement_Clause','Parameter','Requirement_Parameter','REFINED_BY','OUTGOING',graph)

    # adding relationships to satisfying design elements (Signals)
    database_tools.process_relationships(clause_data,'Requirement_Clause','Signal_Name','Requirement_Signal','SATISFY','INCOMING',graph)

    # if domains have correct labels, now add these labels
    if 'domain' in list(req_data.columns):
        # process domains
        input_data = req_data[['uid','domain']]
        
        #drop empty entries
        input_data =  input_data.dropna()

        # Convert data frame to list of dictionaries
        # Neo4j UNWIND query expects a list of dictionaries
        # for bulk insertion
        input_data = list(input_data.T.to_dict().values())
            
        # specifically adding domains for each requirement element
        for row in input_data:
            for domain in row['domain'].split(';'):
                query = """
                        MATCH (n:Requirement {uid:'"""+row['uid']+"""'})-[r]-(n2:Requirement_Clause)-[r2]-(n3:Requirement_Signal)
                        SET n:"""+domain+"""
                                    
                    """
                database_tools.run_neo_query(input_data,query,graph)