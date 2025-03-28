import pandas as pd
import pprint

def process_relationships(data,sourceType,targetKey,targetType,relationshipName,direction,graph):
    """
    Process and add relationships between elements in a Neo4j graph database.

    This function takes data representing relationships between elements and inserts them into a Neo4j
    graph database specified by the 'graph' parameter. It creates relationships between source elements
    of 'sourceType' and target elements of 'targetType' based on the 'targetKey' column in the input DataFrame 'data'.
    The 'relationshipName' parameter specifies the name of the relationship to be created, and the 'direction'
    parameter specifies whether the relationship is outgoing, incoming, or bidirectional.

    @param data: The input DataFrame containing relationship data.
    @type data: pandas.DataFrame

    @param sourceType: The type of the source elements.
    @type sourceType: str

    @param targetKey: The column name in the 'data' DataFrame that contains target element names.
    @type targetKey: str

    @param targetType: The type of the target elements.
    @type targetType: str

    @param relationshipName: The name of the relationship to be created.
    @type relationshipName: str

    @param direction: The direction of the relationship (OUTGOING, INCOMING, or BOTH).
    @type direction: str

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must contain the necessary columns and data for creating relationships.
    @post Relationships are created in the Neo4j graph database based on the specified parameters.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    # adding relationships to available tools
    relation_data = data[['uid',targetKey]]
    relation_data =  relation_data.dropna()

    s = relation_data[targetKey].astype("string").str.split(';').apply(pd.Series, 1).stack()
    s.name = targetKey
    del relation_data[targetKey]
    s = s.to_frame().reset_index()
    relation_data = pd.merge(relation_data, s, right_on='level_0', left_index = True)

    del relation_data["level_0"]
    del relation_data["level_1"]
    relation_data = list(relation_data.T.to_dict().values())

    # uid is used to identify source element, name is used to identify target element

    if direction == "OUTGOING":
        query = """
            UNWIND $rows AS row
                WITH row
                WHERE row."""+ targetKey + """ <> 'NONE'
                MERGE (source:"""+ sourceType + """ {uid:row.uid}) 
                MERGE (target:"""+ targetType + """ {name:row."""+targetKey+"""}) 
                CREATE (source)-[r:"""+ relationshipName+"""]->(target)
 
            """  
    elif direction == "INCOMING":
        query = """
            UNWIND $rows AS row
                WITH row
                WHERE row."""+ targetKey + """ <> 'NONE'
                MERGE (source:"""+ sourceType + """ {uid:row.uid})
                MERGE (target:"""+ targetType + """ {name:row."""+targetKey+"""})
                CREATE (target)-[r:"""+ relationshipName+"""]->(source)       
        """
    else:
        query = """
            UNWIND $rows AS row
            WITH row
            WHERE row."""+ targetKey + """ <> 'NONE'
            MERGE (source:"""+ sourceType + """ {uid:row.uid})
            MERGE (target:"""+ targetType + """ {name:row."""+targetKey+"""})
            CREATE (target)-[r1:"""+ relationshipName+"""]->(source)   
            CREATE (target)<-[r2:"""+ relationshipName+"""]-(source)    
        """
    # WITH and WHERE statements above stop adding relationship to 'NONE' node
    run_neo_query(relation_data,query,graph)

def process_relationships_to_generic(data,sourceType,targetKey,targetType,relationshipName,direction,graph):
    """
    Process and add relationships between elements and generic target elements in a Neo4j graph database.

    This function takes data representing relationships between elements and inserts them into a Neo4j
    graph database specified by the 'graph' parameter. It creates relationships between source elements
    of 'sourceType' and generic target elements of 'targetType' based on the 'targetKey' column in the input DataFrame 'data'.
    The 'relationshipName' parameter specifies the name of the relationship to be created, and the 'direction'
    parameter specifies whether the relationship is outgoing, incoming, or bidirectional.

    @param data: The input DataFrame containing relationship data.
    @type data: pandas.DataFrame

    @param sourceType: The type of the source elements.
    @type sourceType: str

    @param targetKey: The column name in the 'data' DataFrame that contains target element names.
    @type targetKey: str

    @param targetType: The type of the generic target elements.
    @type targetType: str

    @param relationshipName: The name of the relationship to be created.
    @type relationshipName: str

    @param direction: The direction of the relationship (OUTGOING, INCOMING, or BOTH).
    @type direction: str

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @pre The 'data' DataFrame must contain the necessary columns and data for creating relationships.
    @post Relationships are created in the Neo4j graph database with generic target elements based on the specified parameters.

    @see: You can use the neo4j package for interacting with Neo4j databases and pandas for data manipulation.
    """
    # adding relationships to available tools
    relation_data = data[['uid',targetKey]]
    relation_data =  relation_data.dropna()

    s = relation_data[targetKey].str.split(';').apply(pd.Series, 1).stack()
    s.name = targetKey
    del relation_data[targetKey]
    s = s.to_frame().reset_index()
    relation_data = pd.merge(relation_data, s, right_on='level_0', left_index = True)

    del relation_data["level_0"]
    del relation_data["level_1"]
    relation_data = list(relation_data.T.to_dict().values())

    if direction == "OUTGOING":
        query = """
            UNWIND $rows AS row
                WITH row
                WHERE row."""+ targetKey + """ <> 'NONE'
                MERGE (source:"""+ sourceType + """ {uid:row.uid}) 
                MERGE (target:"""+ targetType + """) 
                CREATE (source)-[r:"""+ relationshipName+"""]->(target)
 
            """  
    elif direction == "INCOMING":
        query = """
            UNWIND $rows AS row
            WITH row
            WHERE row."""+ targetKey + """ <> 'NONE'
            MERGE (source:"""+ sourceType + """ {uid:row.name})
            MERGE (target:"""+ targetType + """)
            CREATE (target)<-[r:"""+ relationshipName+"""]-(source)       
        """
    else:
        query = """
            UNWIND $rows AS row
            WITH row
            WHERE row."""+ targetKey + """ <> 'NONE'
            MERGE (source:"""+ sourceType + """ {uid:row.name})
            MERGE (target:"""+ targetType + """)
            CREATE (target)-[r1:"""+ relationshipName+"""]->(source)   
            CREATE (target)<-[r2:"""+ relationshipName+"""]-(source)    
        """
    # WITH and WHERE statements above stop adding relationship to 'NONE' node
    run_neo_query(relation_data,query,graph)
    
def generate_node_match_query(namelist):
    """
    Generate a Neo4j query to match nodes based on a list of names.

    This function takes a list of node names in 'namelist' and generates a Neo4j query to match nodes
    with the corresponding 'uid' property values in the graph database. The query will use the node
    names as variables for matching and return the matched nodes.

    @param namelist: A list of node names to match in the graph database.
    @type namelist: list of str

    @return: A Neo4j query string for matching nodes.
    @rtype: str

    @pre The 'namelist' should contain valid node names that exist in the graph database.

    @see: You can use the neo4j package for interacting with Neo4j databases.
    """
    query = ""
    for name in namelist:
        query = query + "MATCH("+name.replace(" ","_")+"{uid:'"+name+"'}) "

    query = query + "RETURN "
    
    for name in namelist:
        query = query + name.replace(" ","_")+","

    #print('path query:\n')
    #print(query[:-1])
    #print('\n')

    return query[:-1]

def get_batches(lst, batch_size=100):
    """
    Split a list into batches of a specified size.

    This function takes a list 'lst' and splits it into batches of size 'batch_size'. Each batch is represented
    as a tuple containing the starting index and a sublist of 'lst'. The default batch size is 100. NOTE THAT A 
    LIMITED BATCH SIZE MAY CAUSE LOST ENTRIES

    @param lst: The input list to be split into batches.
    @type lst: list

    @param batch_size: The size of each batch (default is 100).
    @type batch_size: int

    @return: A list of tuples, each containing the starting index and a sublist of 'lst'.
    @rtype: list of tuples

    @pre The 'lst' parameter should be a valid list, and 'batch_size' should be a positive integer.

    @see: This function is useful for processing large lists in smaller chunks.
    """
    return [(i, lst[i:i + batch_size]) for i in range(0, len(lst), batch_size)]

def clear_database(graph):
    """
    Clear all nodes and relationships in a Neo4j graph database.

    This function performs a Neo4j query to match and delete all nodes and their relationships
    in the specified graph database. It effectively clears the entire database.

    @param graph: The Neo4j graph database connection to clear.
    @type graph: neo4j.Graph

    @pre Ensure that you have the necessary permissions and take caution when using this function,
         as it will permanently remove all data from the specified graph database.

    @see: You can use the neo4j package for interacting with Neo4j databases.
    """
    query = """
        MATCH(n) DETACH DELETE n
    """
    graph.run(query)

def clear_database_by_label(graph,label):
    """
    Clear all nodes and relationships in a Neo4j graph database.

    This function performs a Neo4j query to match and delete all nodes and their relationships
    in the specified graph database. It effectively clears the entire database.

    @param graph: The Neo4j graph database connection to clear.
    @type graph: neo4j.Graph

    @pre Ensure that you have the necessary permissions and take caution when using this function,
         as it will permanently remove all data from the specified graph database.

    @see: You can use the neo4j package for interacting with Neo4j databases.
    """
    query = """
        MATCH(n:"""+label+""") DETACH DELETE n
    """
    graph.run(query)

def relabel_design_nodes(ignore_name_list,type_label,design_name,result_label,include_design_name,graph):
    """
    Relabel nodes in the Neo4j graph from one design label to another.

    Parameters:
    - type_label (str): The label of the nodes to be relabeled.
    - design_name (str): The name of the design.
    - result_label (str): The label to assign to the relabeled nodes.
    - include_design_name (bool): Indicates whether to include the design name in the label.
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function relabels nodes in the Neo4j graph from one type to another.
    It matches nodes with the specified type label and updates their labels to the specified result label.

    It performs the following steps:
    1. Constructs a Cypher query to match nodes with the specified type label.
    2. Sets or removes the design-specific label based on the 'include_design_name' parameter.
    3. Executes the Cypher query on the Neo4j graph.

    Note:
    - The 'graph' parameter should be a Neo4j graph object representing the database.
    - If 'include_design_name' is True, the nodes will be relabeled with a design-specific label.
    - If 'include_design_name' is False, the nodes will have their design-specific label removed.

    Example usage:
    ```
    relabel_design_nodes("OldLabel", "DesignA", "NewLabel", True, graph)
    ```

    """
    if not include_design_name:
        remove_clause = 'REMOVE n:'+design_name+'_Design_Instance_Element'
    else:
        remove_clause = 'SET n:'+design_name+'_Design_Instance_Element'
    query = """
        MATCH(n:"""+type_label+""":"""+design_name+"""_Design_Instance_Element)
        SET n:"""+result_label+"""_Design_Instance_Element
        """+remove_clause+"""
    """
    #print(query)
    graph.run(query)
    for ignore_name in ignore_name_list:
        query = """
            MATCH(n:"""+type_label+""":"""+result_label+"""_Design_Instance_Element {name:'"""+ignore_name+"""'})
            REMOVE n:"""+result_label+"""_Design_Instance_Element
            SET n:"""+design_name+"""_Design_Instance_Element
        """
        #print(query)
        graph.run(query)

def relabel_design_relationships(type_label,result_label,design_name,graph):
    query = """
        MATCH(n:"""+design_name+"""_Design_Instance_Element)-[r:"""+type_label+"""]->(n2:"""+design_name+"""_Design_Instance_Element)
        CREATE (n)-[r2:"""+result_label+"""]->(n2)
        DELETE r
    """
    graph.run(query)


def run_neo_query(data, query,graph):
    """
    Run a Neo4j query with data in batches.

    This function executes a Neo4j query with a large dataset in batches to prevent memory overload.
    It takes the 'data' parameter as input, splits it into batches, and runs the provided 'query' on each batch
    using the specified 'graph' connection.

    @param data: The data to be used in the query, provided as a list of dictionaries.
    @type data: list

    @param query: The Neo4j query to execute.
    @type query: str

    @param graph: The Neo4j graph database connection.
    @type graph: neo4j.Graph

    @return: The response from the Neo4j query.
    @rtype: neo4j.Result

    @pre The 'data' parameter should contain a list of dictionaries that can be used in the Neo4j query.
    @post The query is executed in batches on the specified graph database.

    @see: You can use the neo4j package for interacting with Neo4j databases.
    """
    batches = get_batches(data)

    for index, batch in batches:
        #print('[Batch: %s] Will cover %s node(s) in Graph' % (index, len(batch)))
        if index == 0:
            response = graph.run(query, rows=batch).data()
        else:
            response.append(graph.run(query, rows=batch).data())
    return response

def apply_constraints(graph):
    """
    Apply constraints to nodes in the Neo4j graph.

    Parameters:
    - graph: The Neo4j graph object representing the database.

    Returns:
    None

    This function applies uniqueness constraints to specific node labels in the Neo4j graph.

    It performs the following steps:
    1. Attempts to create a uniqueness constraint for each specified node label.
    2. Prints any exceptions that occur during constraint creation.

    Note:
    - The 'graph' parameter should be a Neo4j graph object representing the database.

    Example usage:
    ```
    apply_constraints(graph)
    ```

    """
    # Add uniqueness constraints.
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Classifier) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Unit) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Spacecraft) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Subsystem) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Mode) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Comparison) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)
    try:
        graph.run("CREATE CONSTRAINT FOR (c:Difference) REQUIRE c.uid IS UNIQUE;")
    except Exception as e:
        print(e)