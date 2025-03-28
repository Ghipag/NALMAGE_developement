import pydot
from collections import defaultdict
import nalmage.model_generation
import os

def create_plantuml_diagram(model_file_name):
    # adding @startyaml and @endyaml statements to yaml file for diagram

    with open(model_file_name, 'r+') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('@startyaml'.rstrip('\r\n') + '\n' + content)
        # Close the file
        f.close()
    
    with open(model_file_name, 'a') as f:
        f.write('@endyaml')
        # Close the file
        f.close()

    # now running plantuml to generate diagram
    os.system('java -jar plantuml.jar -verbose model_outline.yaml')

def xml_to_dict(t):
    d = {t.tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(xml_to_dict, children):
            for k, v in dc.items():
                dd[k].append(v)
        d = {t.tag: {k: v[0] if len(v) == 1 else v
                     for k, v in dd.items()}}
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            if text:
              d[t.tag]['#text'] = text
        else:
            d[t.tag] = text
    return d

def check_for_populated_entry(str):
    checked_chars = set('\n        ')
    validation = set(str)
    if validation.issubset(checked_chars):
        return False
    else:
        return True

def generate_node_name(element):
    if check_for_populated_entry(element.text):
        name = nalmage.model_generation.remove_illegal_chars(element.text)
    else:
        name = nalmage.model_generation.remove_illegal_chars(element.tag)
    return name

def find_true_parent(parent_nodes,i,node_name,edges):
    parent_name = edges[i][1]
    print(f'initialguess: {parent_name}')
    for j in range(i):
        if parent_nodes[i-j] != node_name:
            parent_name = edges[i-j][1]
            print(f'newguess: {parent_name}')
            break
    return parent_name

def find_true_child(child_nodes,i,node_name,edges):
    child_name = edges[i+1][1]
    print(f'initialguess: {child_name}')
    #for j in range(i):
    #    if child_nodes[i-j] != node_name:
    #        child_name = edges[i-j][1]
    #        print(f'newguess: {child_name}')
    #        break
    return child_name
        

def compute_unique_node_names(edges):
    # idenitifying unique names
    parent_nodes = [row[0] for row in edges]
    child_nodes = [row[1] for row in edges]
    for i in range(len(parent_nodes)):
        # checking child name
        child_name= child_nodes[i]
        child_nodes.pop(i)
        if child_name in child_nodes:
            print(f'FINDINGchild OF {child_name}')
            child_name = child_name + '_' + find_true_child(child_nodes,i,child_name,edges)
        child_nodes.insert(i,child_name)
        # checking parent name
        parent_name= parent_nodes[i]
        parent_nodes.pop(i)
        if parent_name in parent_nodes:
            print(f'FINDINGPARENT OF {parent_name}')
            parent_name = parent_name + '_' + find_true_parent(parent_nodes,i,parent_name,edges)
        parent_nodes.insert(i,parent_name)
    print(parent_nodes)
    print(child_nodes)
    # now inserting new names into the array
    new_edges = []
    for i in range(len(parent_nodes)):
        new_edges.append((parent_nodes[i],child_nodes[i]))
    return new_edges

def create_tree_from_dict(edges,collected_data, parent=None):
    name = next(iter(collected_data.keys()))
    if parent is not None:
        edges.append((parent, name))
    for item in collected_data[name]:
        if isinstance(item, dict):
            get_edges(item, parent=name)
        else:
            edges.append((name, item))


    return edges

def find_edges(edges,collected_data, parent=None):
    if parent is not None:
        name = generate_node_name(collected_data)
        edges.append((parent, name))
        for child in collected_data:
            if str(type(child)) == "<class 'xml.etree.ElementTree.Element'>":
                find_edges(edges,child, parent=name)
            else:
                edges.append((name, child))
    else:
        name = generate_node_name(collected_data.getroot())
        for child in collected_data.getroot():
            if str(type(child)) == "<class 'xml.etree.ElementTree.Element'>":
                find_edges(edges,child, parent=name)
            else:
                edges.append((name, child))

    return edges

def generate_DOT(edges,file_name):
    # Dump edge list in Graphviz DOT format
    with open(file_name, 'w') as f:
        print('strict digraph tree {', file=f)
        for row in edges:

            print('    {0} -> {1};'.format(*row), file=f)
        print('}', file=f)

def draw(graph,parent_name, child_name):
    edge = pydot.Edge(parent_name, child_name)
    graph.add_edge(edge)

def visit(graph,node, parent=None):

    for k,v in node.items():# If using python3, use node.items() instead of node.iteritems()
        if isinstance(v, dict) or isinstance(v, list):
            # We start with the root node whose parent is None
            # we don't want to graph the None node
            if parent:
                draw(graph,parent, k)
            visit(graph,v, k)
        else:
            draw(graph,parent, k)
            # drawing the label using a distinct name
            print(f'k={k}')
            print(f'v={v}')
            draw(graph,k, k+'_'+v)

def get_edges(edges,treedict, parent=None):
   
    if isinstance(treedict,dict):
        print('TREE PART IS DICT')
        name = next(iter(treedict.keys()))
        if parent is not None:
            edges.append((parent, name))
        for item in treedict.items():
            print(f'ITEM IS: {item}')
            print(f'ITEM of TYPE: {type(item)}')
            if isinstance(item, dict):
                get_edges(edges,item, parent=name)
            elif isinstance(item, tuple):
                if isinstance(item[1],str):
                    edges.append((name, item))
                    print(f'ITEM IS BASE TUPLE: {item}')
                else:
                    print(f'ITEM IS LENGTH: {len(item)}')
                    print(f'FIRST INNER ITEM IS: {item[0]}')
                    print(f'SECOND INNER ITEM IS: {item[1]}')
                    get_edges(edges,item[1], parent=name)
            else:
                edges.append((name, item))
    if isinstance(treedict,list):
        print('TREE PART IS LIST')
        name = parent
        if parent is not None:
            edges.append((parent, name))
        for item in treedict:
            print(f'ITEM IS: {item}')
            print(f'ITEM of TYPE: {type(item)}')
            if isinstance(item, dict):
                get_edges(edges,item, parent=name)
            elif isinstance(item, tuple):
                if isinstance(item[1],str):
                    edges.append((name, item))
                    print(f'ITEM IS BASE TUPLE: {item}')
                else:
                    print(f'ITEM IS LENGTH: {len(item)}')
                    print(f'FIRST INNER ITEM IS: {item[0]}')
                    print(f'SECOND INNER ITEM IS: {item[1]}')
                    get_edges(edges,item[1], parent=name)
            else:
                edges.append((name, item))
    return edges