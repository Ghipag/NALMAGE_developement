import pandas as pd
import numpy as np
import networkx as nx
from plotly.offline import iplot
import plotly.graph_objs as go
import plotly.express as px
import database_interaction.database_tools as database_tools

def display_association_rules(labeled_types,results):
    """
    @brief Display association rules graphically.

    This function displays association rules graphically using a network graph visualization. It extracts data from
    the given 'results' object, including rule support, confidence, and lift values, and plots the graph using Plotly
    to visualize the association rules between items.

    @param results A list of association rule results.

    @return None

    @pre 'results' should contain association rule results, typically obtained from association rule mining algorithms.

    @see This function is useful for visually exploring and analyzing association rules between items in a dataset.
    """
    print('displaying variability')
    # loop over results object to extra data
    A = []
    B = []
    edge_Support = []
    edge_Confidence = []
    edge_Lift = []
    single_rule_values = {}

    for item in results:
        # first index of the inner list
        # Contains base item and add item
        pair = item[0] 
        items = [x for x in pair]
        if len(items) == 3:
            A.append(items[0])
            B.append(items[2])
            if len(items)>2:
                A.append(items[1])
                B.append(items[2])
                edge_Support.append(item[1])
                edge_Confidence.append(item[2][0][2])
                edge_Lift.append(item[2][0][3])
                A.append(items[2])
                B.append(items[0])
                edge_Support.append(item[1])
                edge_Confidence.append(item[2][0][2])
                edge_Lift.append(item[2][0][3])
            
        else:
            # if single node rule then assign node specific values
            single_rule_values[items[0]] = [item[1],item[2][0][2],item[2][0][3]]

    node_list = set(A+B)

    # create nxnetwork graph
    G = nx.Graph()

    for i in node_list:
        G.add_node(i)

    for item in results:
        pair = item[0] 
        items = [x for x in pair]
        if len(items) > 1:
            G.add_edges_from([(items[0],items[1])])

    # generate node positions using spring layout
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    for n, p in pos.items():
        G.nodes[n]['pos'] = p

    # adding nodes to the plotly api
    edge_trace_list = []
    edge_index = 0
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_trace = go.Scatter(
        x=[],
        y=[],
        line=dict(width=1,color='#888'), # for variable shading: edge_Support[edge_index]
        hovertext=f'rule confidence is: {edge_Confidence[edge_index]}',
        mode='lines')
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])
        edge_trace_list.append(edge_trace)
        edge_index += 1

        node_trace = go.Scatter(
        x=[],
        y=[],
        text=[],
        mode='markers',
        hoverinfo='text',
        marker_line_color="black",
        marker_line_width=2,
        marker=dict(
            showscale=True,
            colorscale='RdBu',
            reversescale=True,
            color=[],
            size=15,
            colorbar=dict(
                thickness=10,
                title='Single Rule Confidence',
                xanchor='left',
                titleside='right'
            ),
            line=dict(width=0)))

    for node in G.nodes():
        x, y = G.nodes[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

    # colour the nodes according to single node rule values (e.g. confidence)
    node_trace['marker']['symbol'] = []
    for node, adjacencies in enumerate(G.adjacency()):
        parameter = single_rule_values[adjacencies[0]][0]
        if adjacencies[0] in labeled_types:
            node_trace['marker']['symbol']+= tuple([1])
        else:
            node_trace['marker']['symbol']+= tuple([26])
        node_trace['marker']['color']+=tuple([parameter])
        node_info = adjacencies[0] +' Support: '+str(parameter)
        node_trace['text']+=tuple([node_info])
    
    # plot the figure
    traces = edge_trace_list + [node_trace]
    fig = go.Figure(data=traces,
             layout=go.Layout(
                title='Identified Association Rules',
                titlefont=dict(size=16),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    
    fig.update_layout(coloraxis = {'colorscale':'viridis'})

    iplot(fig)

def display_variability_framework_ontology(apriori_rules):
    """
    @brief Display association rules graphically.

    This function displays association rules graphically using a network graph visualization. It extracts data from
    the given 'results' object, including rule support, confidence, and lift values, and plots the graph using Plotly
    to visualize the association rules between items.

    @param results A list of association rule results.

    @return None

    @pre 'results' should contain association rule results, typically obtained from association rule mining algorithms.

    @see This function is useful for visually exploring and analyzing association rules between items in a dataset.
    """
    print('displaying rules')
    # loop over results object to extra data
    A = []
    B = []
    

    relationship_name_list = []
    for rule in apriori_rules:
        if 'may' in rule:
            relationship_name = rule.split('relationship of type ')[1].split(' with')[0]
            A.append(rule.split(' may')[0])
            B.append(rule.split('with ')[1])
            relationship_name_list.append(relationship_name)
        elif 'is' in rule:
            A.append(rule.split(' is')[0])
            B.append(rule.split('is ')[1])
            relationship_name_list.append('SUB_TYPE')


    node_list = set(A+B)

    # create nxnetwork graph
    G = nx.Graph()

    for i in node_list:
        G.add_node(i)

    index = 0
    while index < len(A):
        G.add_edges_from([(A[index],B[index])])
        index += 1

    # generate node positions using spring layout
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    for n, p in pos.items():
        G.nodes[n]['pos'] = p

    # adding nodes to the plotly api
    edge_trace_list = []
    edge_index = 0
    for edge in G.edges():
        x0, y0 = G.nodes[edge[0]]['pos']
        x1, y1 = G.nodes[edge[1]]['pos']
        edge_trace = go.Scatter(
        x=[],
        y=[],
        text=[edge],
        line=dict(width=1,color='#888'),
        hovertext = edge,
        mode='lines')
        edge_trace['x'] += tuple([x0, x1, None])
        edge_trace['y'] += tuple([y0, y1, None])
        edge_trace_list.append(edge_trace)
        edge_index += 1

    node_trace_list = []
    for node in G.nodes():
        node_trace = go.Scatter(
        x=[],
        y=[],
        text=[node],
        mode='markers',
        hoverinfo='text',
        marker_line_color="black",
        marker_line_width=2,
        marker=dict(
            color=["white"],
            size=50,
            line=dict(width=5)))

        # setting positions
        x, y = G.nodes[node]['pos']
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])

        # add to list 
        node_trace_list.append(node_trace)
    
    # plot the figure
    traces = edge_trace_list + node_trace_list
    fig = go.Figure(data=traces,
             layout=go.Layout(
                title='Identified Association Rules',
                titlefont=dict(size=16),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20,l=5,r=5,t=40),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))
    
    fig.update_layout(coloraxis = {'colorscale':'viridis'})

    iplot(fig)

def traverse_comparison_tree(brief_name,comparisons_data,current_comparison,graph):
    """
    @brief Traverse and analyze a comparison tree.

    This function traverses a comparison tree structure, starting from the current comparison node, and collects data
    about the comparisons and their relationships. It counts the number of differences for each comparison and
    generates the necessary data structures for visualization.

    @param brief_name The brief name or identifier for the comparisons.
    @param comparisons_data A dictionary containing data structures for comparisons.
    @param current_comparison The current comparison node to start the traversal.
    @param graph The Neo4j graph database object for querying data.

    @return The updated 'comparisons_data' dictionary with collected data.

    @pre 'comparisons_data' should be initialized with appropriate data structures before calling this function.
    @pre 'current_comparison' should be a valid comparison node in the database.
    @pre 'graph' should be a valid Neo4j graph database connection.

    @see This function is useful for analyzing and visualizing comparison trees, typically generated from a diff
         algorithm.
    """
    # count number of differences
    query = """
        MATCH (n:"""+ brief_name +"""_Comparison {uid:'"""+ current_comparison['n']['uid'] + """'})<-[r:DISCOVERED_BY]-(n1:"""+ brief_name +"""_Difference)
        RETURN count(r)
    """
    
    number_of_differences = database_tools.run_neo_query(['nil'],query,graph)[0] # selecting first comparison from the retrieved list ensures is the "root" comparison
    comparisons_data['difference_count']['link']['value'].append(number_of_differences['count(r)'])
    comparisons_data['difference_count_icicle']['value'].append(number_of_differences['count(r)'])
    # now loop over child comparisons
    query = """
        MATCH (n0:"""+ brief_name +"""_Comparison {uid:'"""+ current_comparison['n']['uid'] + """'})<-[PARENT_COMPARISON]-(n:"""+ brief_name +"""_Comparison)
        RETURN n
    """
    
    child_comparisons = database_tools.run_neo_query(['nil'],query,graph)
    for child in child_comparisons:
        # first generating parent child links
        # find parent index
        parent_index = [index for index, item in enumerate(comparisons_data['difference_count']['node']['label']) if item == generate_reduced_label(current_comparison['n']['uid'])]
        comparisons_data['difference_count']['link']['source'].append(parent_index[0]) # set source as parent comparison
        comparisons_data['difference_count_icicle']['parent'].append(generate_reduced_label(current_comparison['n']['uid']))
        comparisons_data['difference_count']['node']['label'].append(generate_reduced_label(child['n']['uid'])) # create node for current child
        comparisons_data['difference_count_icicle']['label'].append(generate_reduced_label(child['n']['uid']))
        comparisons_data['difference_count_icicle']['type'].append(child['n']['uid'].split('>>')[1])
        comparisons_data['difference_count']['link']['target'].append(len(comparisons_data['difference_count']['node']['label'])-1) # set target as current child comparison
        comparisons_data = traverse_comparison_tree(brief_name,comparisons_data,child,graph)

    return comparisons_data

def generate_reduced_label(comparison_uid):
    """
    @brief Generate a reduced label from a comparison UID.

    This function takes a comparison UID, extracts the label information, and returns a reduced label. The reduced label
    is typically used for visualization or formatting purposes.

    @param comparison_uid The UID of the comparison, containing label information.

    @return The reduced label extracted from the comparison UID.

    @pre 'comparison_uid' should be a valid comparison UID with label information.

    @see This function is useful for generating human-readable labels from comparison UIDs.
    """
    label = comparison_uid.split('->[')[1].replace(']','')
    return label

def acumulate_difference_counts(comparisons_data):
    """
    @brief Accumulate difference counts for comparisons in a tree structure.

    This function takes a comparisons data structure representing a tree of comparisons and their difference counts.
    It accumulates the difference counts along the tree structure to compute cumulative difference counts.

    @param comparisons_data A dictionary containing information about comparisons and their difference counts.

    @return The updated comparisons_data dictionary with cumulative difference counts.

    @pre The input 'comparisons_data' should be a valid dictionary structure representing comparisons and their difference counts.
    @post The returned dictionary will include cumulative difference counts for the comparisons in the tree structure.

    @see This function is useful for computing cumulative difference counts in a hierarchical structure of comparisons.
    """
    comparisons_data['cumulative_difference_count'] = {}
    comparisons_data['cumulative_difference_count']['node'] = {}
    comparisons_data['cumulative_difference_count']['node']['label'] = []
    comparisons_data['cumulative_difference_count']['node']['colour'] = []
    comparisons_data['cumulative_difference_count']['link'] = {}
    comparisons_data['cumulative_difference_count']['link']['source'] = []
    comparisons_data['cumulative_difference_count']['link']['target'] = []
    comparisons_data['cumulative_difference_count']['link']['value'] = []
    comparisons_data['cumulative_difference_count']['link']['label'] = []
    comparisons_data['cumulative_difference_count']['link']['colour'] = []

    # now count back through the existing link entries and reverse through the tree, accumulating link values (difference counts) as we go
    link_index = len(comparisons_data['difference_count']['link']['target'])-1
    while link_index >= 0:
        print(f'link index is: {link_index}')
        # if exists, add to difference count
        current_source_index = comparisons_data['difference_count']['link']['source'][link_index]
        current_target_index = comparisons_data['difference_count']['link']['target'][link_index]
        current_value = comparisons_data['difference_count']['link']['target'][link_index]

        if comparisons_data['difference_count']['node']['label'][current_source_index] in comparisons_data['cumulative_difference_count']['node']['label']:
            # find index of the existing accumulating node
            existing_index = comparisons_data['cumulative_difference_count']['node']['label'].index(comparisons_data['difference_count']['node']['label'][current_source_index])
            print(f' exisitng index is:{existing_index}')
            comparisons_data['cumulative_difference_count']['link']['value'][existing_index] = comparisons_data['cumulative_difference_count']['link']['value'][existing_index] + current_value
        
        # else if new label, add node , with source and target and set difference count
        else:
            print(f'generating entry for: {comparisons_data["difference_count"]["node"]["label"][current_source_index]}')
            comparisons_data['cumulative_difference_count']['node']['label'].append(comparisons_data['difference_count']['node']['label'][current_source_index])
            comparisons_data['cumulative_difference_count']['link']['source'].append(current_source_index)
            comparisons_data['cumulative_difference_count']['link']['target'].append(current_target_index)
            comparisons_data['cumulative_difference_count']['link']['value'].append(current_value)


        link_index -= 1
        
    return comparisons_data

def plot_sankey(comparisons_data,plot_key):
    """
    @brief Plot a Sankey diagram based on the provided comparisons data.

    This function generates a Sankey diagram from the given comparisons data using Plotly.

    @param comparisons_data A dictionary containing information about comparisons and their links.

    @param plot_key A string indicating the key within the comparisons_data dictionary to be used for plotting.

    @pre The input 'comparisons_data' should be a valid dictionary structure representing comparisons and their links.
    @pre The 'plot_key' should correspond to a valid key in 'comparisons_data'.

    @post The function will display a Sankey diagram based on the specified 'plot_key'.

    @see This function is useful for visualizing hierarchical relationships or flows represented in the comparisons data.
    """
    fig = go.Figure(data=[go.Sankey(
        node = dict(
        pad = 15,
        thickness = 20,
        line = dict(color = "black", width = 0.5),
        label =  comparisons_data[plot_key]['node']['label'],
        color = "blue"
        ),
        link = dict(
        source =  comparisons_data[plot_key]['link']['source'],
        target =  comparisons_data[plot_key]['link']['target'],
        value =  comparisons_data[plot_key]['link']['value']
    ))])

    fig.update_layout(title_text=plot_key+" Sankey Diagram", font_size=10)
    fig.show()


def comparison_diff_count_sankey_diagrams(brief_name,graph):
    """
    @brief Generate and display Sankey diagrams for difference counts in comparison data.

    This function calculates and displays Sankey diagrams for difference counts in the given comparison data.

    @param brief_name A string representing the brief name of the comparison data.

    @param graph The Neo4j graph database containing the comparison data.

    @return A dictionary containing information about the calculated difference counts and Sankey diagrams.

    @pre The input 'brief_name' should be a valid string representing the comparison data.

    @pre The input 'graph' should be a valid Neo4j graph database containing the comparison data.

    @post The function will display Sankey diagrams based on difference counts and return a dictionary with related data.

    @see This function is useful for visualizing the distribution of differences within comparison data.
    """
    # firstly need to loop thorough comparison tree and count differences at each comparison
    # start at root node (spacecraft) and compare differences at each node recursively
    comparisons_data = {}
    comparisons_data['difference_count'] = {}
    comparisons_data['difference_count']['node'] = {}
    comparisons_data['difference_count']['node']['label'] = []
    comparisons_data['difference_count']['node']['colour'] = []
    comparisons_data['difference_count']['link'] = {}
    comparisons_data['difference_count']['link']['source'] = []
    comparisons_data['difference_count']['link']['target'] = []
    comparisons_data['difference_count']['link']['value'] = []
    comparisons_data['difference_count']['link']['label'] = []
    comparisons_data['difference_count']['link']['colour'] = []
    comparisons_data['difference_count_icicle'] = {}
    comparisons_data['difference_count_icicle']['label'] = []
    comparisons_data['difference_count_icicle']['parent'] = []
    comparisons_data['difference_count_icicle']['value'] = []
    comparisons_data['difference_count_icicle']['type'] = []



    query = """
        MATCH (n:"""+ brief_name +"""_Comparison)
        RETURN n
    """
    # doing basic count of differences
    current_comparison = database_tools.run_neo_query(['nil'],query,graph)[0] # selecting first comparison from the retrieved list ensures is the "root" comparison
    comparisons_data['difference_count']['node']['label'].append(generate_reduced_label(current_comparison['n']['uid']))
    comparisons_data['difference_count_icicle']['label'].append(generate_reduced_label(current_comparison['n']['uid']))
    comparisons_data['difference_count_icicle']['type'].append(current_comparison['n']['uid'].split('>>')[1])
    comparisons_data['difference_count_icicle']['parent'].append('')
    comparisons_data = traverse_comparison_tree(brief_name,comparisons_data,current_comparison,graph)

    # doing cumulative count of difference
    #comparisons_data = acumulate_difference_counts(comparisons_data) # is broken

    
    # plot diagrams
    plot_sankey(comparisons_data,'difference_count')
    #plot_sankey(comparisons_data,'cumulative_difference_count')

    return comparisons_data

def comparison_diff_count_icile_plots(comparisons_data,):
    """
    @brief Generate and display an Icicle Plot for difference counts in comparison data.

    This function calculates and displays an Icicle Plot for difference counts in the given comparison data.

    @param comparisons_data A dictionary containing information about the calculated difference counts and hierarchy.

    @return The input dictionary containing the difference count information.

    @pre The input 'comparisons_data' should be a dictionary with the required structure.

    @post The function will display an Icicle Plot based on the provided difference count data.

    @see This function is useful for visualizing the hierarchical structure of difference counts.
    """
    # directly plotting comparisons in icicle plot
    fig =px.icicle(
        comparisons_data['difference_count_icicle'],
        names='label',
        parents='parent',
        values='value',
        color='type',
    )
    fig.update_traces(root_color="lightgreen")
    fig.update_layout(margin = dict(t=50, l=25, r=25, b=25))
    fig.update_layout(title_text="Direct Icile Diagram", font_size=10)
    fig.show()

    return comparisons_data

def comparison_diff_count_pie_charts(comparisons_data):
    """
    @brief Generate and display pie charts for difference counts related to comparison types.

    This function calculates and displays two pie charts:
    - One pie chart shows the number of differences related to each comparison type.
    - Another pie chart shows the number of comparisons related to each comparison type.

    @param comparisons_data A dictionary containing information about the calculated difference counts and hierarchy.

    @return The input dictionary containing the difference count information.

    @pre The input 'comparisons_data' should be a dictionary with the required structure.

    @post The function will display two pie charts based on the provided data.

    @see This function is useful for visualizing the distribution of differences and comparisons among comparison types.
    """
    comparisons_data['type_counts']= {}
    comparisons_data['type_counts']['labels'] = []
    comparisons_data['type_counts']['counts'] = []
    comparisons_data['type_counts']['comparisons'] = []
    comp_index = 0
    while comp_index < len(comparisons_data['difference_count_icicle']['type']):
        entry = comparisons_data['difference_count_icicle']['type'][comp_index]
        if entry in comparisons_data['type_counts']['labels']:
            entry_index = [index for index, item in enumerate(comparisons_data['type_counts']['labels']) if item == entry]
            comparisons_data['type_counts']['counts'][entry_index[0]] += comparisons_data['difference_count_icicle']['value'][comp_index]
            comparisons_data['type_counts']['comparisons'][entry_index[0]] += 1
        else:
            comparisons_data['type_counts']['labels'].append(entry)
            comparisons_data['type_counts']['comparisons'].append(1)
            comparisons_data['type_counts']['counts'].append(comparisons_data['difference_count_icicle']['value'][comp_index])
        comp_index += 1
    fig = px.pie(comparisons_data['type_counts'], values='counts', names='labels', title='number of differences related to each comparison type')
    fig.show()
    fig = px.pie(comparisons_data['type_counts'], values='comparisons', names='labels', title='number of comparisons related to each comparison type')
    fig.show()
    return comparisons_data