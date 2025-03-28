import database_interaction.database_tools as database_tools
import networkx as nx
from network2tikz import plot


def export_design_to_edge_list(graph, design_name,file_name):
    """
    @brief Export a specific design from a Neo4j graph database to an edge list file.

    This function executes a Neo4j query to retrieve the edges of a specific design and exports them as an edge list
    to a text file.

    @param graph The Neo4j graph database connection.
    @param design_name The name of the design to export.
    @param file_name The name of the file to which the edge list will be exported.

    @return None

    @pre 'graph' should be a valid Neo4j graph database connection.
    @pre 'design_name' should be a valid design name existing in the graph.
    @pre 'file_name' should be a valid file name.

    @see This function is useful for exporting the edges of a specific design from a Neo4j graph database
         to an edge list format, which can be used for further analysis.
    """
    query = """
            MATCH(n:"""+design_name+"""_Design_Instance_Element)-[r]-(n2:"""+design_name+"""_Design_Instance_Element) 
            RETURN n.uid,n2.uid,r.id
              
        """
    responses = database_tools.run_neo_query(['nil'],query,graph)
    with open(f'exported_graphs/{file_name}', "w") as text_file:
        for pair in responses:
            text_file.write(f'{pair["n.uid"]} {pair["n2.uid"]}\n')

def export_query_subgraph_to_tikz(graph, query,colour_dict,file_name):
    """
    @brief Export a specific design from a Neo4j graph database to an edge list file.

    This function executes a Neo4j query to retrieve the edges of a specific design and exports them as an edge list
    to a text file.

    @param graph The Neo4j graph database connection.
    @param design_name The name of the design to export.
    @param file_name The name of the file to which the edge list will be exported.

    @return None

    @pre 'graph' should be a valid Neo4j graph database connection.
    @pre 'design_name' should be a valid design name existing in the graph.
    @pre 'file_name' should be a valid file name.

    @see This function is useful for exporting the edges of a specific design from a Neo4j graph database
         to an edge list format, which can be used for further analysis.
    """
    # subject nodes as n, object nodes as n2, predicates as r
    query = "MATCH(n:AVDASI_2020_S1_Design_Instance_Element)-[r:PARENT]-(n2:AVDASI_2020_S1_Design_Instance_Element) RETURN n,n2,r"

    query=query+', type(r) as r_types, labels(n) as n_types, labels(n2) as n2_types'
    responses = database_tools.run_neo_query(['nil'],query,graph)
    vertex_records = []

    
    for triple in responses:
        vertex_records.append((triple['n']['name'],triple['n2']['name'],{'type': triple['r_types']}))
    
    G=nx.DiGraph()
    G.add_edges_from(vertex_records)
    pos = nx.kamada_kawai_layout(G)

    

    # getting relationship types
    types = []
    for n, nbrs in G.adj.items():
        for nbr, eattr in nbrs.items():
            types.append(eattr['type'].replace('_',' '))

    # getting node types
    node_names = []
    node_types = []
    for entry in list(G):
        # find current node type from responses
        for triple in responses:
            if triple['n']['name'] == entry:
                for label in triple['n_types']:
                    if label in colour_dict.keys():
                        node_types.append(label)
                        break
                break
            elif triple['n2']['name'] == entry:
                for label in triple['n2_types']:
                    if label in colour_dict.keys():
                        node_types.append(label)
                        break
                break

        entry = entry.replace('_',' ')
        node_names.append(entry)

    # visuual stype settings
    visual_style = {}
    visual_style['vertex_size'] = .5
    visual_style['vertex_color'] = [colour_dict[g] for g in node_types]
    #visual_style['vertex_opacity'] = .7
    visual_style['vertex_label'] = node_names
    #visual_style['edge_label'] = types
    #visual_style['edge_label_position'] =  'below'
    #visual_style['edge_label_size'] = '0.4'
    visual_style['vertex_label_position'] = 'left'
    visual_style['edge_curved'] = 0.1
    visual_style['layout'] = pos
    visual_style['canvas'] = (10,10)
    visual_style['margin'] = 2.5
    plot(G,file_name+'.tikz','tex',**visual_style)




def export_comparison_to_edge_list(graph, mission_name,file_name):
    """
    @brief Export comparisons from a Neo4j graph database to an edge list file.

    This function executes Neo4j queries to retrieve comparisons and their relationships to differences and exports them
    as an edge list to a text file.

    @param graph The Neo4j graph database connection.
    @param mission_name The name of the mission or comparison group.
    @param file_name The name of the file to which the edge list will be exported.

    @return None

    @pre 'graph' should be a valid Neo4j graph database connection.
    @pre 'mission_name' should be a valid mission or comparison group name existing in the graph.
    @pre 'file_name' should be a valid file name.

    @see This function is useful for exporting comparisons and their relationships from a Neo4j graph database
         to an edge list format, which can be used for further analysis.
    """
    query = """
            MATCH(n:"""+mission_name+"""_Comparison)-[r]-(n2:"""+mission_name+"""_Comparison)
            RETURN n.uid,n2.uid,r.id
              
        """
    responses_comp_2_comp = database_tools.run_neo_query(['nil'],query,graph)

    query = """
            MATCH(n:"""+mission_name+"""_Comparison)-[r]-(n2:"""+mission_name+"""_Difference)
            RETURN n.uid,n2.uid,r.id
              
        """
    responses_comp_2_diff = database_tools.run_neo_query(['nil'],query,graph)
    with open(f'exported_graphs/{file_name}', "w") as text_file:
        for pair in responses_comp_2_comp:
            text_file.write(f'{pair["n.uid"].split("->")[1].replace(">","").replace(",","").replace(" ","_").replace("[","").replace("]","")} {pair["n2.uid"].split("->")[1].replace(">","").replace(",","").replace(" ","_").replace("[","").replace("]","")}\n')
        for pair in responses_comp_2_diff:
            pair["n.uid"]
            pair["n2.uid"]
            text_file.write(f'{pair["n.uid"].split("->")[1].replace(">","").replace(",","").replace(" ","_").replace("[","").replace("]","")} {pair["n2.uid"].replace(">","").replace(",","").replace(" ","_").replace("[","").replace("]","")}\n')
        

def export_all_designs_to_edge_list(graph,missions_list):
    """
    @brief Export all designs and comparisons from Neo4j graph database to edge list files.

    This function exports all designs and their relationships in the specified missions, as well as comparisons
    between designs, to edge list files for further analysis.

    @param graph The Neo4j graph database connection.
    @param missions_list A dictionary containing mission names as keys and lists of designs within each mission as values.

    @return None

    @pre 'graph' should be a valid Neo4j graph database connection.
    @pre 'missions_list' should be a dictionary where keys are mission names, and values are lists of design names
         existing in the graph.

    @see This function is useful for exporting designs and comparisons from a Neo4j graph database to edge list format,
         which can be used for various types of analysis.
    """
    for mission, designs in missions_list.items():
        export_comparison_to_edge_list(graph, mission,mission+'.txt')
        for design in designs:
            export_design_to_edge_list(graph, design,design+'.txt')
