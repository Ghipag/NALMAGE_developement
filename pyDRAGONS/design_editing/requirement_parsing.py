import subprocess
import os
import shutil
import pprint
import pandas as pd
import sys
sys.path.insert(1, 'C:/Users/lt17550/nlp_reform/nlp_reform_sem_sim/modules')

def parse_mission_requirements(mission_name):
    # collect current working directory
    cwd = os.getcwd()

    # copy across input data
    shutil.copyfile(f'data/{mission_name}_Requirement_Info.xlsx', 'C:/Users/lt17550/nlp_reform/data/Input.xlsx')

    # change directory to nlp reform location
    os.chdir('C:/Users/lt17550/nlp_reform')
    # activate venv then run parser program
    subprocess.call(["C:/Users/lt17550/nlp_reform/.venv/Scripts/python.exe", "C:/Users/lt17550/nlp_reform/parse_requirements.py"])
    # return to original directory
    os.chdir(cwd)

    # collect output data
    shutil.copyfile('C:/Users/lt17550/nlp_reform/data/Output.xlsx',f'data/{mission_name}_Parsed_Requirement_Info.xlsx')

def parse_signals(mission_name):
    clauses = ['goal']
    signals = [{'name': 'Miss_Compliant', 'data_type': 'Boolean', 'desc': 'Event: Mission is compliant'}, {'name': 'Miss_Goal', 'data_type': 'Boolean', 'desc': 'Event: Mission is goal compliant'}, {'name': 'Nom_Life', 'data_type': 'single', 'desc': 'nominal lifetime'}]
    # collect current working directory
    cwd = os.getcwd()

    # copy across input data
    shutil.copyfile(f'data/{mission_name}_Requirement_Info.xlsx', 'C:/Users/lt17550/nlp_reform/data/Input.xlsx')

    # change directory to nlp reform location
    os.chdir('C:/Users/lt17550/nlp_reform')
    # activate venv then run parser program
    response = subprocess.check_output(["C:/Users/lt17550/nlp_reform/.venv/Scripts/python.exe", "C:/Users/lt17550/nlp_reform/identify_satisfy_relationships.py "+str(clauses)+" "+str(signals)])
    print(response)
    # return to original directory
    os.chdir(cwd)

    # collect output data
    shutil.copyfile('C:/Users/lt17550/nlp_reform/data/Output.xlsx',f'data/{mission_name}_Parsed_Requirement_Info.xlsx')