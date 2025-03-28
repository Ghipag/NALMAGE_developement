import pandas as pd
from . import database_tools

def run_valid_neo_query(data,query,graph):
    # currently no ontology checks to do
    database_tools.run_neo_query(data,query,graph)

def create_valid_relationship(row,sourceType,targetKey,targetType,relationshipName,Ontology_Relationship,invalid_label_flag,invalid_relationship_label,leading_direction_character,post_direction_character,graph):
    """
    @brief Create valid relationships between nodes based on certain conditions.

    This function creates relationships between nodes in a Neo4j graph database based on specified conditions.
    It can also handle marking nodes as invalid when certain conditions are met.

    @param row A dictionary containing data related to the relationship.
    @param sourceType The type of the source node in the relationship.
    @param targetKey The key used to identify the target node.
    @param targetType The type of the target node in the relationship.
    @param relationshipName The name of the relationship to be created.
    @param Ontology_Relationship The name of the ontology relationship.
    @param invalid_label_flag A flag indicating whether the invalid label exists.
    @param invalid_relationship_label The label to be used for invalid relationships.
    @param leading_direction_character The character for the leading direction in the relationship.
    @param post_direction_character The character for the post direction in the relationship.
    @param graph The Neo4j graph database instance.

    @pre The input parameters should be properly formatted and consistent with the database schema.
    @post The function will create relationships between nodes and may mark nodes as invalid based on conditions.

    @see This function is useful for managing relationships and node validity in a Neo4j graph database.
    """
    # setting invalid markers
    query = """
        MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'})-[r:CLASSIFIER]-(target_classifier)
        WITH target,target_classifier
        MATCH (target_classifier)-[r:"""+Ontology_Relationship+"""]->("""+Ontology_Relationship+"""_classifier)
        WITH target,target_classifier,"""+Ontology_Relationship+"""_classifier
        MATCH (source:"""+ sourceType + """ {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(source_classifier)
        WITH """+Ontology_Relationship+"""_classifier,source,source_classifier,target,target_classifier,"""+Ontology_Relationship+"""_classifier.uid AS """+Ontology_Relationship+"""_classifier_uid
        WITH source_classifier.uid AS source_classifier,"""+Ontology_Relationship+"""_classifier_uid,source,target,target_classifier
        WHERE source_classifier <> """+Ontology_Relationship+"""_classifier_uid
        SET 
            target:Invalid
        """
    database_tools.run_neo_query([row],query,graph)

    query = """
        MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'})-[r:CLASSIFIER]-(target_classifier)
        WITH target,target_classifier
        MATCH (target_classifier)-[r:"""+Ontology_Relationship+"""]->("""+Ontology_Relationship+"""_classifier)
        WITH target,target_classifier,"""+Ontology_Relationship+"""_classifier
        MATCH (source:"""+ sourceType + """ {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(source_classifier)
        WITH """+Ontology_Relationship+"""_classifier,source,source_classifier,target,target_classifier,"""+Ontology_Relationship+"""_classifier.uid AS """+Ontology_Relationship+"""_classifier_uid
        WITH source_classifier.uid AS source_classifier,"""+Ontology_Relationship+"""_classifier_uid,source,target,target_classifier
        WHERE source_classifier <> """+Ontology_Relationship+"""_classifier_uid
        SET 
            target:"""+invalid_relationship_label+"""
        """
    database_tools.run_neo_query([row],query,graph)

    # setting valid markers
    query = """
        MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'})-[r:CLASSIFIER]-(target_classifier)
        WITH target,target_classifier
        MATCH (target_classifier)-[r:"""+Ontology_Relationship+"""]->("""+Ontology_Relationship+"""_classifier)
        WITH target,target_classifier,"""+Ontology_Relationship+"""_classifier
        MATCH (source:"""+ sourceType + """ {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(source_classifier)
        WITH """+Ontology_Relationship+"""_classifier,source,source_classifier,source_classifier.uid AS source_classifier_uid,target,target_classifier,"""+Ontology_Relationship+"""_classifier.uid AS """+Ontology_Relationship+"""_classifier_uid
        WHERE source_classifier_uid = """+Ontology_Relationship+"""_classifier_uid
        SET target:Valid_"""+Ontology_Relationship+"""_to_"""+row['uid'].replace('-','')+"""
        CREATE (target)"""+leading_direction_character+"""-[r:"""+ relationshipName+"""]-"""+post_direction_character+"""(source)
        REMOVE 
            target:"""+invalid_relationship_label+"""
        """
    database_tools.run_neo_query([row],query,graph)

    # only removing Invalid label if it didn't exist before and current relationship is valid
    # original (pre batching fix): if str(invalid_label_flag) == '(No data)':
    if not invalid_label_flag:
        query = """
            MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'})-[r:CLASSIFIER]-(target_classifier)
            WITH target,target_classifier
            MATCH (target_classifier)-[r:"""+Ontology_Relationship+"""]->("""+Ontology_Relationship+"""_classifier)
            WITH target,target_classifier,"""+Ontology_Relationship+"""_classifier
            MATCH (source:"""+ sourceType + """ {uid:'"""+row['uid']+"""'})-[r:CLASSIFIER]-(source_classifier)
            WITH """+Ontology_Relationship+"""_classifier,source,source_classifier,source_classifier.uid AS source_classifier_uid,target,target_classifier,"""+Ontology_Relationship+"""_classifier.uid AS """+Ontology_Relationship+"""_classifier_uid
            WHERE source_classifier_uid = """+Ontology_Relationship+"""_classifier_uid
            REMOVE 
                target:Invalid
            """
        database_tools.run_neo_query([row],query,graph)

def process_valid_relationships(data,sourceType,targetKey,targetType,relationshipName,Ontology_Relationship,direction,graph):
    """
    @brief Process and create valid relationships between nodes based on specified conditions.

    This function processes data and creates valid relationships between nodes in a Neo4j graph database based on specified conditions.
    It also checks if relationships are allowed according to ontology rules.

    @param data The data containing information about the relationships to be created.
    @param sourceType The type of the source node in the relationship.
    @param targetKey The key used to identify the target node.
    @param targetType The type of the target node in the relationship.
    @param relationshipName The name of the relationship to be created.
    @param Ontology_Relationship The name of the ontology relationship.
    @param direction The direction of the relationship (OUTGOING, INCOMING, or BOTH).
    @param graph The Neo4j graph database instance.

    @pre The input data should be properly formatted and consistent with the database schema.
    @post The function will create valid relationships between nodes based on specified conditions.

    @see This function is useful for processing and creating relationships in a Neo4j graph database while considering ontology rules.
    """
    # need to identify if relationship is allowed according to ontology
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
    
    # firstly find children classifiers
    # then find those classifier's allowed owners and check if matches current node
    # uid is used to identify source element, name is used to identify target element
    if direction == 'OUTGOING':
        leading_direction_character = ''
        post_direction_character = '>'
    elif direction == 'INCOMING':
        leading_direction_character = '<'
        post_direction_character = ''
    else:
        leading_direction_character = '<'
        post_direction_character = """(source)
        CREATE (target)-[r2:"""+ relationshipName+"""]->
        """

    general_parameters = ['ontology/Mass','ontology/Power','ontology/Length','ontology/Data_Generation','ontology/Function']

    for row in relation_data:
        # need to check these is an actual relationship
        if row[targetKey] != 'NONE':

            # check for pre-existing invalid label
            query = """
                MATCH (target{name:'"""+row[targetKey]+"""'})
                WHERE target:Invalid AND  target:Design_Instance_Element
                RETURN target
                """
            invalid_label_flag = database_tools.run_neo_query([row],query,graph)

            invalid_relationship_label = 'Invalid_'+Ontology_Relationship+'_to_'+row['uid'].replace('-','').replace('/','')

            # check if current source is a general parameter e.g. mass or power that could belong to any spacecraft, subsystem or unit
            # only need to check if considering ownership relations
            if relationshipName == 'PARENT':
                # currently the dirty solution is to simply not check if allowed in the ontology and just applying these relationships right away
                query = """
                    MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'})-[r:CLASSIFIER]-(target_classifier)
                    RETURN target_classifier
                    """
                #print(query)
                target_classifier = database_tools.run_neo_query([row],query,graph)
                try:
                    if target_classifier[0]['target_classifier']['uid'] in general_parameters:
                        # immediately setting valid markers
                        #print(f'skipping ontology check for target: {row[targetKey]}')
                        query = """
                            MATCH (target:"""+ targetType + """ {name:'"""+row[targetKey]+"""'}), (source:"""+ sourceType + """ {uid:'"""+row['uid']+"""'})
                            SET target:Valid_"""+Ontology_Relationship+"""_to_"""+row['uid'].replace('-','')+"""
                            CREATE (target)"""+leading_direction_character+"""-[r:"""+ relationshipName+"""]-"""+post_direction_character+"""(source)
                            REMOVE 
                                target:"""+invalid_relationship_label+"""
                            """
                        database_tools.run_neo_query([row],query,graph)
                    
                    else:
                        create_valid_relationship(row,sourceType,targetKey,targetType,relationshipName,Ontology_Relationship,invalid_label_flag,invalid_relationship_label,leading_direction_character,post_direction_character,graph)
                except:
                    # useful if made mistake in input files
                    print('****Look here****')
                    print(f'target type is: {targetType}')
                    print(f'target key is: {row[targetKey]}')
                    print(f'target classifier is: {target_classifier}')
                    print('ERROR IN INPUT FILES')
                    exit()
                    
            else:
                create_valid_relationship(row,sourceType,targetKey,targetType,relationshipName,Ontology_Relationship,invalid_label_flag,invalid_relationship_label,leading_direction_character,post_direction_character,graph)
            

            