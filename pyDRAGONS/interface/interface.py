import tkinter as tk
from PIL import Image,ImageTk
from pyDRAGONS.design_problem_formulation import product_line_engineering as product_line_engineering
from pyDRAGONS.design_problem_formulation import design_problem_query_tools as design_problem_query_tools
import pyperclip
import uuid
from tkinter import ttk
from colorama import init as colorama_init
from colorama import Fore
from colorama import Style
colorama_init()

def initialise():
    """
    Initialize the GUI application.

    Creates and configures the main GUI window with a specified title,
    maximum size, and background color.

    Returns:
        tk.Tk: The root window of the GUI application.
    """
    root = tk.Tk()
    root.maxsize(900, 600)  # specify the max size the window can expand to
    root.config(bg="grey16")  # specify background color
    return root

def display_processing_progress(root,task_name,progress):
    return root
    
def display_diagram_commands(root,missions_list):
    """
    Display a GUI for generating diagram commands.

    Args:
        root (tk.Tk): The root window of the GUI application.
        missions_list (dict): A dictionary containing missions and their associated designs.

    Returns:
        None
    """
    root.title("Diagram Command Generator")  # title of the GUI window
    design_names =[]
    missions = []
    for mission, designs in missions_list.items():
        missions.append(mission)
        for design in designs:
            design_names.append(design)

    results_page = tk.Frame(root,width=900, height=600, bg='grey')
    results_page.grid(row=0, column=0, padx=10, pady=5)
    left_frame = tk.Frame(results_page,width=200, height=400, bg='grey')
    left_frame.grid(row=0, column=0, padx=10, pady=5)
    #.tkraise()

    # quit bottom
    button = tk.Button(left_frame, 
                        text="Quit", 
                        fg="red",
                        command=quit)
    button.grid(row=0, column=0, padx=5, pady=3, ipadx=10)

    middle_frame = tk.Frame(left_frame,width=180, height=185,bg="white")
    middle_frame.grid(row=2, column=0, padx=5, pady=5)
    tk.Label(middle_frame, text="Diagrams").grid(row=0, column=0, padx=10, pady=5)

    # check button for displaying requirement links
    show_satisfy = tk.IntVar()
    c1 = tk.Checkbutton(middle_frame, text='include satisfy relations to requirements',variable=show_satisfy, onvalue=True, offvalue=False)
    c1.grid(row=1, column=0, padx=5, pady=3, ipadx=10)


    # design selection for diagram generation
    variable = tk.StringVar(root)
    variable.set(design_names[0]) # default value

    des2 = tk.StringVar(root)
    des2.set(design_names[-1]) # default value

    mission = tk.StringVar(root)
    mission.set(missions[0]) # default value

    right_frame = tk.Frame(results_page, width=650, height=400, bg='grey16')
    right_frame.grid(row=0, column=1, padx=10, pady=5)

    lower_frame = tk.Frame(right_frame, width=650, height=190, bg='lightgrey')
    lower_frame.grid(row=0, column=0, padx=10, pady=5)
    tk.Label(lower_frame, text="Designs").grid(row=0,column=0, padx=5, pady=5)

    # design diagram selection
    w = tk.OptionMenu(lower_frame, variable, *design_names)
    w.grid(row=1, column=0, padx=10, pady=5)

    lower1_frame = tk.Frame(right_frame, width=650, height=190, bg='lightgrey')
    lower1_frame.grid(row=1, column=0, padx=10, pady=5)
    tk.Label(lower1_frame, text="Design Comparison").grid(row=0,column=0, padx=5, pady=5)

    # design 2 selection
    w2 = tk.OptionMenu(lower1_frame, des2, *design_names)
    w2.grid(row=1, column=0, padx=10, pady=5)

    # mission selection
    w3 = tk.OptionMenu(lower1_frame, mission, *missions)
    w3.grid(row=2, column=0, padx=10, pady=5)
    

    image = (Image.open("interface/Logo - colour PNG.png"))
    resized_image= image.resize((int(886/4),int(256/4)), Image.LANCZOS)
    new_image= ImageTk.PhotoImage(resized_image)
    tk.Label(right_frame, image=new_image).grid(row=2, column=0, padx=2, pady=2)
    

    # defining button command functions
    def copy_overview_command():
        if show_satisfy.get() == True:
            pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r]-(n2:{variable.get()}_Design_Instance_Element),(n3:{variable.get()}_Design_Instance_Element)-[r2:SATISFY]-(n4:{mission.get()}_Requirement_Element) RETURN n,n2,n3,n4,r,r2')
        elif show_satisfy.get() == False:
            pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')
        
    def copy_rd_command():
        pyperclip.copy(f'MATCH(n:{mission.get()}_Requirement_Element)-[r]-(n2:{mission.get()}_Requirement_Element) RETURN n,n2,r')

    def copy_bdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:PARENT]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')
    
    def copy_fbd_command():
        pyperclip.copy(f'MATCH(n:Function:{variable.get()}_Design_Instance_Element)-[r]-(n2:{variable.get()}_Design_Instance_Element),(na:Function:{variable.get()}_Design_Instance_Element)-[ra:SATISFY]-(n2a:{mission.get()}_Requirement_Element) RETURN n,n2,r,na,n2a,ra')

    def copy_power_ibdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:POWER_INTERFACE]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')
    
    def copy_data_ibdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:DATA_INTERFACE]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')

    def copy_mechanical_ibdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:MECHANICAL_INTERFACE]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')

    def copy_fluid_ibdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:FLUID_INTERFACE]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')

    def copy_thermal_ibdd_command():
        pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r:THERMAL_INTERFACE]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')

    def copy_parameter_table_command():
        pyperclip.copy(f'MATCH(p:Parameter) WHERE p:{variable.get()}_Design_Instance_Element RETURN p.uid,p.Value')

    def copy_ontology_command():
        pyperclip.copy(f'MATCH(n:Classifier)-[r]-(n2:Classifier) RETURN n,n2,r')

    def copy_shared_classifier_command():
        pyperclip.copy(f'MATCH (n:{variable.get()}_vs_{des2.get()}_SHARED_Classifier)-[r:CLASSIFIER]-(c:Classifier)  RETURN n,r,c')

    def copy_dissimilar_classifier_command():
        joint_label_name = variable.get()+'_vs_'+des2.get()+'_SHARED_Classifier'
        query = """
            MATCH (n1:"""+variable.get()+"""_Design_Instance_Element),(n2:"""+des2.get()+"""_Design_Instance_Element)
            WHERE NOT n1:"""+joint_label_name+""" AND NOT n2:"""+joint_label_name+"""
            RETURN n1, n2
            """
        pyperclip.copy(query)
    
    def copy_shared_parameter_command():
        query = """
        MATCH (n1:"""+variable.get()+"""_vs_"""+des2.get()+"""_SHARED_Parameter)-[:CLASSIFIER]-(c:Classifier)-[:CLASSIFIER]-(n2:"""+variable.get()+"""_vs_"""+des2.get()+"""_SHARED_Parameter),
        (n1:"""+variable.get()+"""_Design_Instance_Element)-[r1:PARENT]-(ownern1:"""+variable.get()+"""_Design_Instance_Element),
        (n2:"""+des2.get()+"""_Design_Instance_Element)-[r2:PARENT]-(ownern2:"""+des2.get()+"""_Design_Instance_Element),
        (owner_classifier:Classifier)
        WHERE (ownern1)-[:CLASSIFIER]->(owner_classifier) AND (ownern2)-[:CLASSIFIER]->(owner_classifier)
        RETURN n1.uid,n1.Value,n2.uid,n2.Value,n1.Value-n2.Value
        """
        pyperclip.copy(query)

    def copy_display_comparisons_and_differences_command():
        pyperclip.copy(f'MATCH(c:{mission.get()}_Comparison)-[r]-(d:{mission.get()}_Difference),(c2:{mission.get()}_Comparison)-[r2:PARENT_COMPARISON]-(c3:{mission.get()}_Comparison) RETURN c,r,d,c2,r2,c3')

    # generating buttons for diagram types
    # overview
    overview_button = tk.Button(middle_frame, 
                    text="Overview", 
                    fg="black",
                    command=copy_overview_command)
    overview_button.grid(row=2, column=0, padx=5, pady=3, ipadx=10)

    # rd
    overview_button = tk.Button(middle_frame, 
                    text="Requirements", 
                    fg="black",
                    command=copy_rd_command)
    overview_button.grid(row=3, column=0, padx=5, pady=3, ipadx=10)

    # bdd
    overview_button = tk.Button(middle_frame, 
                    text="System Breakdown", 
                    fg="black",
                    command=copy_bdd_command)
    overview_button.grid(row=4, column=0, padx=5, pady=3, ipadx=10)

    # fbd
    overview_button = tk.Button(middle_frame, 
                    text="Functional Breakdown", 
                    fg="black",
                    command=copy_fbd_command)
    overview_button.grid(row=5, column=0, padx=5, pady=3, ipadx=10)

    # power_ibdd
    overview_button = tk.Button(middle_frame, 
                    text="Power Architecture", 
                    fg="black",
                    command=copy_power_ibdd_command)
    overview_button.grid(row=6, column=0, padx=5, pady=3, ipadx=10)

    # data_ibdd
    overview_button = tk.Button(middle_frame, 
                    text="Data Architecture", 
                    fg="black",
                    command=copy_data_ibdd_command)
    overview_button.grid(row=7, column=0, padx=5, pady=3, ipadx=10)

    # mechanical_ibdd
    overview_button = tk.Button(middle_frame, 
                    text="mechanical Architecture", 
                    fg="black",
                    command=copy_mechanical_ibdd_command)
    overview_button.grid(row=8, column=0, padx=5, pady=3, ipadx=10)

    # fluid_ibdd
    overview_button = tk.Button(middle_frame, 
                    text="Fluid Architecture", 
                    fg="black",
                    command=copy_fluid_ibdd_command)
    overview_button.grid(row=9, column=0, padx=5, pady=3, ipadx=10)

    # thermal_ibdd
    overview_button = tk.Button(middle_frame, 
                    text="Thermal Architecture", 
                    fg="black",
                    command=copy_thermal_ibdd_command)
    overview_button.grid(row=10, column=0, padx=5, pady=3, ipadx=10)

    # parameter_table
    overview_button = tk.Button(middle_frame, 
                    text="Parameter Table", 
                    fg="black",
                    command=copy_parameter_table_command)
    overview_button.grid(row=11, column=0, padx=5, pady=3, ipadx=10)

    # ontology
    overview_button = tk.Button(middle_frame, 
                    text="Ontology", 
                    fg="grey",
                    command=copy_ontology_command)
    overview_button.grid(row=12, column=0, padx=5, pady=3, ipadx=10)

    # generating buttons for design comparisons
    # shared classifiers
    overview_button = tk.Button(lower1_frame, 
                    text="Display Shared Classfiers", 
                    fg="black",
                    command=copy_shared_classifier_command)
    overview_button.grid(row=3, column=0, padx=5, pady=3, ipadx=10)

    # dissimilar classifiers
    overview_button = tk.Button(lower1_frame, 
                    text="Display Dissimilar Classifiers", 
                    fg="black",
                    command=copy_dissimilar_classifier_command)
    overview_button.grid(row=4, column=0, padx=5, pady=3, ipadx=10)

    # similar Parameters
    overview_button = tk.Button(lower1_frame, 
                    text="Display Shared Parameters", 
                    fg="black",
                    command=copy_shared_parameter_command)
    overview_button.grid(row=5, column=0, padx=5, pady=3, ipadx=10)

    # comparisons and differences
    overview_button = tk.Button(lower1_frame, 
                    text="Display Comparisons and Differences", 
                    fg="black",
                    command=copy_display_comparisons_and_differences_command)
    overview_button.grid(row=6, column=0, padx=5, pady=3, ipadx=10)

    root.mainloop()


def initialise_editor_explorer():
    """
    Initialize the GUI application.

    Creates and configures the editor GUI window with a specified title,
    maximum size, and background color.

    Returns:
        tk.Tk: The root window of the GUI application.
    """
    root = tk.Tk()
    root.title("Design Editor and Explorer")  # title of the GUI window
    root.maxsize(900, 600)  # specify the max size the window can expand to
    root.config(bg="grey16")  # specify background color
    return root

def display_editor_commands(root,missions_list):
    """
    Display a GUI for generating diagram commands.

    Args:
        root (tk.Tk): The root window of the GUI application.
        missions_list (dict): A dictionary containing missions and their associated designs.

    Returns:
        None
    """
    design_names =[]
    missions = []
    for mission, designs in missions_list.items():
        missions.append(mission)
        for design in designs:
            design_names.append(design)

    results_page = tk.Frame(root,width=900, height=600, bg='grey')
    results_page.grid(row=0, column=0, padx=10, pady=5)
    left_frame = tk.Frame(results_page,width=200, height=400, bg='grey')
    left_frame.grid(row=0, column=0, padx=10, pady=5)
    #.tkraise()

    # quit button
    button = tk.Button(left_frame, 
                        text="Quit", 
                        fg="red",
                        command=quit)
    button.grid(row=0, column=0, padx=5, pady=3, ipadx=10)

    middle_frame = tk.Frame(left_frame,width=180, height=185,bg="white")
    middle_frame.grid(row=2, column=0, padx=5, pady=5)
    tk.Label(middle_frame, text="Diagrams").grid(row=0, column=0, padx=10, pady=5)


    # design feature selection
    variable = tk.StringVar(root)
    variable.set(design_names[0]) # default value

    des2 = tk.StringVar(root)
    des2.set(design_names[-1]) # default value

    mission = tk.StringVar(root)
    mission.set(missions[0]) # default value

    right_frame = tk.Frame(results_page, width=650, height=400, bg='grey16')
    right_frame.grid(row=0, column=1, padx=10, pady=5)

    lower_frame = tk.Frame(right_frame, width=650, height=190, bg='lightgrey')
    lower_frame.grid(row=0, column=0, padx=10, pady=5)
    tk.Label(lower_frame, text="Design Element Type to Query").grid(row=0,column=0, padx=5, pady=5)

    # design diagram selection
    w = tk.OptionMenu(lower_frame, variable, *design_names)
    w.grid(row=1, column=0, padx=10, pady=5)

    lower1_frame = tk.Frame(right_frame, width=650, height=190, bg='lightgrey')
    lower1_frame.grid(row=1, column=0, padx=10, pady=5)
    tk.Label(lower1_frame, text="Design Comparison").grid(row=0,column=0, padx=5, pady=5)

    # design 2 selection
    w2 = tk.OptionMenu(lower1_frame, des2, *design_names)
    w2.grid(row=1, column=0, padx=10, pady=5)


    image = (Image.open("interface/Logo - colour PNG.png"))
    resized_image= image.resize((int(886/4),int(256/4)), Image.LANCZOS)
    new_image= ImageTk.PhotoImage(resized_image)
    tk.Label(right_frame, image=new_image).grid(row=2, column=0, padx=2, pady=2)
    

    # defining button command functions
    def copy_overview_command():
        if show_satisfy.get() == True:
            pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r]-(n2:{variable.get()}_Design_Instance_Element),(n3:{variable.get()}_Design_Instance_Element)-[r2:SATISFY]-(n4:{mission.get()}_Requirement_Element) RETURN n,n2,n3,n4,r,r2')
        elif show_satisfy.get() == False:
            pyperclip.copy(f'MATCH(n:{variable.get()}_Design_Instance_Element)-[r]-(n2:{variable.get()}_Design_Instance_Element) RETURN n,n2,r')
        
    # generating buttons for diagram types
    # overview
    overview_button = tk.Button(middle_frame, 
                    text="Overview", 
                    fg="black",
                    command=copy_overview_command)
    overview_button.grid(row=2, column=0, padx=5, pady=3, ipadx=10)


    root.mainloop()

# functions for dict display in design play ground 
def json_tree(tree, parent, dictionary):
    for key in dictionary:
        uid = uuid.uuid4()
        if isinstance(dictionary[key], dict):
            tree.insert(parent, 'end', uid, text=key)
            json_tree(tree, uid, dictionary[key])
        elif isinstance(dictionary[key], list):
            tree.insert(parent, 'end', uid, text=key + '[]')
            json_tree(tree,
                      uid,
                      dict([(i, x) for i, x in enumerate(dictionary[key])]))
        else:
            value = dictionary[key]
            if value is None:
                value = 'None'
            tree.insert(parent, 'end', uid, text=key, value=value)


def show_query_data(data):
    # Setup the root UI
    root = tk.Tk()
    root.title("JSON viewer")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Setup the Frames
    tree_frame = ttk.Frame(root, padding="3")
    tree_frame.grid(row=0, column=0, sticky=tk.NSEW)

    # Setup the Tree
    tree = ttk.Treeview(tree_frame, columns='Values')
    tree.column('Values', width=100, anchor='center')
    tree.heading('Values', text='Values')
    json_tree(tree, '', data)
    tree.pack(fill=tk.BOTH, expand=1)

    # Limit windows minimum dimensions
    root.update_idletasks()
    root.minsize(800, 800)
    root.mainloop()

def secondary_feature_string_section(design_name,secondary_type):
    if '[existing]' in secondary_type.get():
        query_string_section = "{uid:'"+design_name+secondary_type.get().split(' ')[0]+"'}"
    else:
        query_string_section = ':' + secondary_type.get().split(' ')[0]
    return query_string_section

def display_product_line(root,completed_query,design_name,mission_name,graph,variability_framework):
    root.title("Design Space And Product Line Information")  
    main_page = tk.Frame(root,width=900, height=600, bg='grey')
    main_page.grid(row=0, column=0, padx=10, pady=5)
    top_frame = tk.Frame(main_page,width=200, height=400, bg='grey')
    top_frame.grid(row=0, column=0, padx=10, pady=5)
    tk.Label(top_frame, text="Query Control").grid(row=0, column=0, padx=10, pady=5) 
    left_frame = tk.Frame(main_page,width=200, height=400, bg='grey')
    left_frame.grid(row=1, column=0, padx=10, pady=5)
    #.tkraise()

    # quit bottom
    button = tk.Button(top_frame, 
                        text="Quit", 
                        fg="red",
                        command=quit)
    button.grid(row=1, column=0, padx=5, pady=3, ipadx=10)

    # query input
    req_root = tk.Tk()
    req_root.maxsize(900, 600)  # specify the max size the window can expand to
    req_root.config(bg="grey16")
    req_listbox_in = tk.Listbox(req_root, height='5')
    req_listbox_in.grid(row=0, column=0, padx=10, pady=10)
    req_listbox_out = tk.Listbox(req_root, height='5')
    req_listbox_out.grid(row=0, column=2, padx=(0,10), pady=10)
    dep_label = tk.Label(req_root, text='requirement selection (use arrow keys)')
    dep_label.grid(row=5, column=0, columnspan=3, pady=(0,10))
    des_root = tk.Tk()
    des_root.maxsize(900, 600)  # specify the max size the window can expand to
    des_root.config(bg="grey16")
    des_listbox_in = tk.Listbox(des_root, height='5')
    des_listbox_in.grid(row=0, column=0, padx=10, pady=10)
    des_listbox_out = tk.Listbox(des_root, height='5')
    des_listbox_out.grid(row=0, column=2, padx=(0,10), pady=10)
    dep_label = tk.Label(des_root, text='design variable selection (use arrow keys)')
    dep_label.grid(row=5, column=0, columnspan=3, pady=(0,10))
    dep_root = tk.Tk()
    dep_root.maxsize(900, 600)  # specify the max size the window can expand to
    dep_root.config(bg="grey16")
    dep_listbox_in = tk.Listbox(dep_root, height='5')
    dep_listbox_in.grid(row=4, column=0, padx=10, pady=10)
    dep_listbox_out = tk.Listbox(dep_root, height='5')
    dep_listbox_out.grid(row=4, column=2, padx=(0,10), pady=10)
    dep_label = tk.Label(dep_root, text='dependant variable selection (use arrow keys)')
    dep_label.grid(row=5, column=0, columnspan=3, pady=(0,10))

    req_list = product_line_engineering.list_requirement_names(graph)
    query_type_list = ['Requirement to Function SA','Function to Component SA','Function to Mode SA','Functional decomposition SA','Internal Interfaces Analysis','Parametric Analysis']
    design_element_list = product_line_engineering.list_design_element_names(design_name,graph)

    for item in req_list:
        req_listbox_in.insert(tk.END, item)

    for item in design_element_list:
        des_listbox_in.insert(tk.END, item)
        dep_listbox_in.insert(tk.END, item)

    def select_req(event=None):
        req_listbox_out.insert(tk.END, req_listbox_in.get(tk.ANCHOR))
        req_listbox_in.delete(tk.ANCHOR)

    def deselect_req(event=None):
        req_listbox_in.insert(tk.END, req_listbox_out.get(tk.ANCHOR))
        req_listbox_out.delete(tk.ANCHOR)

    req_root.bind('<Right>', select_req)
    req_root.bind('<Left>', deselect_req)

    def select_des(event=None):
        des_listbox_out.insert(tk.END, des_listbox_in.get(tk.ANCHOR))
        des_listbox_in.delete(tk.ANCHOR)

    def deselect_des(event=None):
        des_listbox_in.insert(tk.END, des_listbox_out.get(tk.ANCHOR))
        des_listbox_out.delete(tk.ANCHOR)

    des_root.bind('<Right>', select_des)
    des_root.bind('<Left>', deselect_des)

    def select_dep(event=None):
        dep_listbox_out.insert(tk.END, dep_listbox_in.get(tk.ANCHOR))
        dep_listbox_in.delete(tk.ANCHOR)

    def deselect_dep(event=None):
        dep_listbox_in.insert(tk.END, dep_listbox_out.get(tk.ANCHOR))
        dep_listbox_out.delete(tk.ANCHOR)

    dep_root.bind('<Right>', select_dep)
    dep_root.bind('<Left>', deselect_dep)

    # query type selection
    query_type_selection = tk.StringVar(root)
    query_type_selection.set(query_type_list[0])
    w = tk.OptionMenu(top_frame,query_type_selection,*query_type_list)
    w.grid(row=2, column=0, padx=10, pady=5)

    selection_frame = tk.Frame(left_frame,width=180, height=185,bg="white")
    selection_frame.grid(row=1, column=0, padx=5, pady=5)
    tk.Label(selection_frame, text="Selection Control").grid(row=0, column=0, padx=10, pady=5) 

    middle_frame = tk.Frame(left_frame,width=180, height=185,bg="white")
    middle_frame.grid(row=2, column=0, padx=5, pady=5)
    tk.Label(middle_frame, text="Load Features").grid(row=0, column=0, padx=10, pady=5) 

    # active design variable selection
    design_variable = tk.StringVar(root)
    possible_design_variables = []

    for design_variable_key in completed_query['design variable'].keys():
        possible_design_variables.append(design_variable_key)
    
    design_variable.set(possible_design_variables[0])
    w = tk.OptionMenu(selection_frame,design_variable,*possible_design_variables)
    w.grid(row=1, column=0, padx=10, pady=5)

    # relationship type
    relationship_type = tk.StringVar(root)
    possible_relationship_types = ['PARENT','INTERFACE [general]','DATA_INTERFACE','POWER_INTERFACE','MECHANICAL_INTERFACE','FLUID_INTERFACE']
    
    relationship_type.set(possible_relationship_types[0])
    
    # primary feature selection
    primary_type = tk.StringVar(root)
    def identify_possible_feature_types():
        possible_primary_type = []
        if relationship_type.get() == 'PARENT':
            for entry_key in completed_query['additional model elements']['children'].keys():
                for addition in completed_query['additional model elements']['children'][entry_key]:
                    additional_type = addition['type']
                    feature_type = product_line_engineering.check_feautre_type(additional_type,variability_framework)
                    possible_primary_type.append(additional_type+' ['+feature_type+']')
        
        elif relationship_type.get() == 'DATA_INTERFACE':
            for des_var_key in completed_query['suggested dependant variable'].keys():
                for neighbour_key in completed_query['suggested dependant variable'][des_var_key].keys():
                    print(neighbour_key)
                    for feature in completed_query['suggested dependant variable'][des_var_key][neighbour_key]:
                        if not isinstance(feature, str) and 'relationship' in feature.keys() and feature['relationship'] == relationship_type.get():
                            print(feature)
                            feature_type = feature['type']
                            possible_primary_type.append(feature_type)

        return possible_primary_type

    def identify_possible_feature_types_with_query(query):
        possible_primary_type = []
        if relationship_type.get() == 'PARENT':
            for entry_key in query['additional model elements']['children'].keys():
                for addition in query['additional model elements']['children'][entry_key]:
                    additional_type = addition['type']
                    feature_type = product_line_engineering.check_feautre_type(additional_type,variability_framework)
                    possible_primary_type.append(additional_type+' ['+feature_type+']')
        
        elif relationship_type.get() == 'DATA_INTERFACE':
            for des_var_key in query['suggested dependant variable'].keys():
                for neighbour_key in query['suggested dependant variable'][des_var_key].keys():
                    print(neighbour_key)
                    for feature in query['suggested dependant variable'][des_var_key][neighbour_key]:
                        if not isinstance(feature, str) and 'relationship' in feature.keys() and feature['relationship'] == relationship_type.get():
                            print(feature)
                            feature_type = feature['type']
                            possible_primary_type.append(feature_type)

        return possible_primary_type

    possible_primary_type = identify_possible_feature_types()

        # feature explanation selection
    feature_explain_selection = tk.StringVar(root)
    feature_explain_selection.set(possible_primary_type[0])
    w = tk.OptionMenu(top_frame,feature_explain_selection,*possible_primary_type)
    w.grid(row=3, column=0, padx=10, pady=5)

    # now list existing design elements
    possible_secondary_types = possible_primary_type # include possible additional types
    possible_secondary_types = product_line_engineering.list_existing_features(possible_secondary_types,design_name,graph)

    # tick box for mandatory/optional control
    opt_mand = tk.StringVar()

    c1 = tk.Checkbutton(selection_frame, text='optional/mandatory',variable=opt_mand, onvalue='optional', offvalue='mandatory')
    c1.grid(row=5, column=0, padx=5, pady=3, ipadx=10)

    def update_optional_mandatory(primary_type_value):
        opt_mand.set(primary_type_value.split('[')[1].replace(']',''))

    primary_type.set(possible_primary_type[0])
    primary_om = tk.OptionMenu(selection_frame,primary_type,*possible_primary_type,command=update_optional_mandatory)
    primary_om.grid(row=3, column=0, padx=10, pady=5)

    # secondary feature selection
    secondary_type = tk.StringVar(root)
    secondary_type.set(possible_primary_type[0])
    secondary_om = tk.OptionMenu(selection_frame,secondary_type,*possible_secondary_types)
    secondary_om.grid(row=4, column=0, padx=10, pady=5)

    # refresh feature menus
    def refresh_feats(new_relationship_type):
        # Reset var and delete all old options
        primary_om['menu'].delete(0, 'end')

        # Insert list of new options (tk._setit hooks them up to var)
        # primary feats
        primary_feats = identify_possible_feature_types()
        primary_type.set(primary_feats[0])
        
        for choice in primary_feats:
            primary_om['menu'].add_command(label=choice, command=tk._setit(primary_type, choice))

        # secondary feats
        secondary_feats = primary_feats
        secondary_feats = product_line_engineering.list_existing_features(secondary_feats,design_name,graph)
        secondary_type.set(secondary_feats[0])
        secondary_om['menu'].delete(0, 'end')

        for choice in secondary_feats:
            secondary_om['menu'].add_command(label=choice, command=tk._setit(secondary_type, choice))
    
    def refresh_feats_onquery_run(query):
        # Reset var and delete all old options
        primary_om['menu'].delete(0, 'end')

        # Insert list of new options (tk._setit hooks them up to var)
        # primary feats
        primary_feats = identify_possible_feature_types_with_query(query)
        primary_type.set(primary_feats[0])
        
        for choice in primary_feats:
            primary_om['menu'].add_command(label=choice, command=tk._setit(primary_type, choice))

        # secondary feats
        secondary_feats = primary_feats
        secondary_feats = product_line_engineering.list_existing_features(secondary_feats,design_name,graph)
        secondary_type.set(secondary_feats[0])
        secondary_om['menu'].delete(0, 'end')

        for choice in secondary_feats:
            secondary_om['menu'].add_command(label=choice, command=tk._setit(secondary_type, choice))

    # add option menu for relationship type 
    w = tk.OptionMenu(selection_frame,relationship_type,*possible_relationship_types, command = refresh_feats)
    w.grid(row=2, column=0, padx=10, pady=5)

    # run query bottom
    def run_query():
        design_query = {'query type':query_type_selection.get(),'requirement':req_listbox_out.get(0, tk.END),'design variable':des_listbox_out.get(0, tk.END),'dependant variable':dep_listbox_out.get(0, tk.END),'additional model elements':[]}
        completed_query,log_record = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,design_name,graph)
        refresh_feats_onquery_run(completed_query)
    
    # run query bottom
    def explain_feature():
        feature_to_explain = feature_explain_selection.get().split(' [')[0]
        print(f'explanation of {Fore.RED}{feature_to_explain}')
        design_problem_query_tools.generate_result_explanation([feature_to_explain],True,design_name)

    button = tk.Button(top_frame, 
                        text="Explain Feature", 
                        fg="black",
                        command=explain_feature)
    button.grid(row=4, column=0, padx=5, pady=3, ipadx=10)

    button = tk.Button(top_frame, 
                        text="run Query", 
                        fg="red",
                        command=run_query)
    button.grid(row=5, column=0, padx=5, pady=3, ipadx=10)

    # load optional/ mandatory feature
    def load_optional_mandatory_feature():
        pyperclip.copy("MATCH(des_var {uid:'"+design_name+design_variable.get()+"'}) MERGE(des_var)-[r:"+opt_mand.get()+"_FEATURE]->(additional_element:Feature:"+primary_type.get().split(' ')[0]+")")

    load_button = tk.Button(middle_frame, 
                    text="load optional/mandatory feature", 
                    fg="black",
                    command=load_optional_mandatory_feature)
    load_button.grid(row=2, column=0, padx=5, pady=3, ipadx=10)

    # load as alternative feature
    def load_alternative_feature():
        pyperclip.copy("MATCH(des_var {uid:'"+design_name+design_variable.get()+"'}) MERGE(des_var)-[r:ALTERNATIVE_FEATURE]->(additional_element:Feature:"+primary_type.get().split(' ')[0]+")")

    load_button = tk.Button(middle_frame, 
                    text="load alternative feature", 
                    fg="black",
                    command=load_alternative_feature)
    load_button.grid(row=3, column=0, padx=5, pady=3, ipadx=10)

    # mark required feature
    def mark_required_feature():
        query_string_section = secondary_feature_string_section(design_name,secondary_type)
        pyperclip.copy("MATCH(pri_feat:"+primary_type.get().split(' ')[0]+") MATCH(sec_feat"+query_string_section+") MERGE(pri_feat)-[r:REQUIRED_FEATURE]->(sec_feat)")

    load_button = tk.Button(middle_frame, 
                    text="mark required feature", 
                    fg="black",
                    command=mark_required_feature)
    load_button.grid(row=4, column=0, padx=5, pady=3, ipadx=10)

    # mark conflicting feature
    def mark_conflicting_feature():
        pyperclip.copy("MATCH(pri_feat:"+primary_type.get().split(' ')[0]+") MATCH(sec_feat:"+secondary_type.get().split(' ')[0]+") MERGE(pri_feat)-[r:CONFLICT_FEATURE]->(sec_feat)")

    load_button = tk.Button(middle_frame, 
                    text="mark conflicting feature", 
                    fg="black",
                    command= mark_conflicting_feature)
    load_button.grid(row=5, column=0, padx=5, pady=3, ipadx=10)


    root.mainloop()