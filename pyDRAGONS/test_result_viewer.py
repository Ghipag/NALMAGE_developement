import json
import pprint
import variability_framework_testing
import load_designs
import database_interaction.database_tools as database_tools
from py2neo import Graph
import os
import pandas as pd
import statistics
from tqdm import tqdm

def load_current_set(path_to_json = 'test_results/'):
    # this finds our json files
    json_files = [pos_json for pos_json in os.listdir(path_to_json) if pos_json.endswith('.json')]

    return json_files,path_to_json
    
def process_section_results(json_files,path_to_json):
    average_precision = []
    average_recall = []
    elements_of_concern = []
    parameter_test_results = []
    compliance_test_results = []
    elements_of_concern_dict = {}
    results_per_relationship_type_per_design = {}
    average_parameter_precision = []
    average_parameter_recall = []
    parameter_elements_of_concern = []
    parameter_elements_of_concern_dict = {}
    parameter_results_per_relationship_type_per_design = {}
    results_per_query_type_per_design = {}
    list_of_tested_requirements = []
    

    # we need both the json and an index number so use enumerate()
    for index, js in enumerate(json_files):
        with open(os.path.join(path_to_json, js)) as json_file:
            results = json.load(json_file)
            if '_justification_' in js:
                current_precision,current_recall,current_elements_of_concern,results_per_relationship_type,results_per_query_type =  variability_framework_testing.aggregate_results(results)
                results_per_relationship_type_per_design[js] = results_per_relationship_type  
                results_per_query_type_per_design[js] = results_per_query_type              
                elements_of_concern.extend(current_elements_of_concern)
                elements_of_concern_dict[js] = current_elements_of_concern
                average_precision.append(current_precision)
                average_recall.append(current_recall)
            elif '_parameter_' in js:
                current_parameter_precision,current_parameter_recall,current_parameter_elements_of_concern,parameter_results_per_relationship_type,results_per_query_type =  variability_framework_testing.aggregate_results(results)
                parameter_results_per_relationship_type_per_design[js] = parameter_results_per_relationship_type                
                parameter_elements_of_concern.extend(current_parameter_elements_of_concern)
                parameter_elements_of_concern_dict[js] = current_parameter_elements_of_concern
                average_parameter_precision.append(current_parameter_precision)
                average_parameter_recall.append(current_parameter_recall)
                for requirement_key in results.keys():
                    for transation_key in results[requirement_key]["SATISFY"].keys():
                        if results[requirement_key]["SATISFY"][transation_key]['grab_set']:
                            list_of_tested_requirements.append(requirement_key)

            elif '_compliance_' in js:
                compliance_test_results.append(results['result'])

    # now average across each relationship type
    averages_per_relationship_type = {}
    for design in results_per_relationship_type_per_design.keys():
        for relationship_type in results_per_relationship_type_per_design[design].keys():
            if not relationship_type in averages_per_relationship_type.keys():
                averages_per_relationship_type[relationship_type] = {'precision':0,'recall':0,'precision_averages':[],'recall_averages':[]}
            if results_per_relationship_type_per_design[design][relationship_type]['average_precision'] != 'NO TEST':
                averages_per_relationship_type[relationship_type]['precision_averages'].append(results_per_relationship_type_per_design[design][relationship_type]['average_precision'])
                averages_per_relationship_type[relationship_type]['recall_averages'].append(results_per_relationship_type_per_design[design][relationship_type]['average_recall'])

    for relationship_type in averages_per_relationship_type.keys():
        #need to handle case where no realtionship types occured in design
        try:
            averages_per_relationship_type[relationship_type]['precision'] = sum(averages_per_relationship_type[relationship_type]['precision_averages'])/len(averages_per_relationship_type[relationship_type]['precision_averages'])*100
            averages_per_relationship_type[relationship_type]['recall'] = sum(averages_per_relationship_type[relationship_type]['recall_averages'])/len(averages_per_relationship_type[relationship_type]['recall_averages'])*100
            averages_per_relationship_type[relationship_type].pop('precision_averages', None)
            averages_per_relationship_type[relationship_type].pop('recall_averages', None)
        except:
            averages_per_relationship_type[relationship_type]['precision'] = 'NONE'
            averages_per_relationship_type[relationship_type]['recall'] = 'NONE'
            averages_per_relationship_type[relationship_type].pop('precision_averages', None)
            averages_per_relationship_type[relationship_type].pop('recall_averages', None)

    # now average across each query type
    averages_per_query_type = {}
    for design in results_per_query_type_per_design.keys():
        for query_type in results_per_query_type_per_design[design].keys():
            if not query_type in averages_per_query_type.keys():
                averages_per_query_type[query_type] = {'precision':0,'recall':0,'precision_averages':[],'recall_averages':[]}
            if results_per_query_type_per_design[design][query_type]['average_precision'] != 'NO TEST':
                averages_per_query_type[query_type]['precision_averages'].append(results_per_query_type_per_design[design][query_type]['average_precision'])
                averages_per_query_type[query_type]['recall_averages'].append(results_per_query_type_per_design[design][query_type]['average_recall'])

    for query_type in averages_per_query_type.keys():
        #need to handle case where no realtionship types occured in design
        try:
            averages_per_query_type[query_type]['precision'] = sum(averages_per_query_type[query_type]['precision_averages'])/len(averages_per_query_type[query_type]['precision_averages'])*100
            averages_per_query_type[query_type]['recall'] = sum(averages_per_query_type[query_type]['recall_averages'])/len(averages_per_query_type[query_type]['recall_averages'])*100
            averages_per_query_type[query_type].pop('precision_averages', None)
            averages_per_query_type[query_type].pop('recall_averages', None)
        except:
            averages_per_query_type[query_type]['precision'] = 'NONE'
            averages_per_query_type[query_type]['recall'] = 'NONE'
            averages_per_query_type[query_type].pop('precision_averages', None)
            averages_per_query_type[query_type].pop('recall_averages', None)

    averages_per_relationship_type = pd.DataFrame(averages_per_relationship_type)
    averages_per_query_type = pd.DataFrame(averages_per_query_type)
    pprint.pprint(elements_of_concern_dict)
    print(f'number of concerning elements: {len(elements_of_concern)}')
    pprint.pprint(averages_per_relationship_type)
    pprint.pprint(averages_per_query_type)
    print(f'average precisions:{average_precision}')
    if len(average_precision) != 0:
        print(f'total average precision: {sum(average_precision)/len(average_precision)*100}%')
    print(f'average recalls: {average_recall}')
    if len(average_recall) != 0:
        print(f'total average recall: {sum(average_recall)/len(average_recall)*100}%')
    if len(parameter_test_results) != 0:
        print(f'average parameter test success: {sum(parameter_test_results)/len(parameter_test_results)*100}%')
    compliance_test_average = 0
    if len(compliance_test_results) != 0:
        compliance_test_average = sum(compliance_test_results)/len(compliance_test_results)
        print(f'average compliance test result: {compliance_test_average*100}%')
    print(f'average parameter precisions:{average_parameter_precision}')
    if len(average_parameter_precision) != 0:
        print(f'total average parameter precision: {sum(average_parameter_precision)/len(average_parameter_precision)*100}%')
    print(f'average parameter recalls: {average_parameter_recall}')
    if len(average_parameter_recall) != 0:
        print(f'total average parameter recall: {sum(average_parameter_recall)/len(average_parameter_recall)*100}%')
    print(f'No. requirements tested with parameter tests: {len(list_of_tested_requirements)}')
    # to compare 
    #MATCH (a:Parameter:ESA_Proj_Design_Design_Instance_Element) WHERE NOT (a)-[:PARENT]->() RETURN a

    # collecting results into dict
    total_results = {}
    total_results['elements of concern dict'] = elements_of_concern_dict
    total_results['averages per relationship type'] = averages_per_relationship_type
    total_results['averages per query type'] = averages_per_query_type
    total_results['average precision'] = average_precision
    total_results['average recall'] = average_recall
    total_results['parameter test results'] = parameter_test_results
    total_results['compliance test average'] =  compliance_test_average
    total_results['parameter elements of concern dict'] = parameter_elements_of_concern_dict
    total_results['average parameter precision'] = average_parameter_precision
    total_results['average parameter recall'] = average_parameter_recall
    total_results['compliance test results'] = compliance_test_results
    return total_results

def flatten(xss):
    return [x for xs in xss for x in xs]

def select_result_files(path_to_res,group,select_list):
    candidate_json_files = [pos_json for pos_json in os.listdir(path_to_res+group+'/test_results') if pos_json.endswith('.json')]
    json_files = []
    for candidate in candidate_json_files:
        if any(name in candidate for name in select_list):
            json_files.append(candidate)
    return json_files

def take_dataframe_average_robust(dataframe_list):
    # create result dataframe based on first
    result_dataframe = dataframe_list[0].copy()
    # no set all values to 0 
    for col in result_dataframe.columns:
        result_dataframe[col].values[:] = 0
    
    # go by collum, then data frame
    for column in result_dataframe.columns.values:
        column_entry_count = 0
        for dataframe in dataframe_list:
            for index, row in dataframe.iterrows():
                if row[column] != 'NONE':
                    column_entry_count += 0.5 # 0.5 as two rows in these tables
                    result_dataframe[column][index] += row[column]
        # now divide by number of entires for this column
        result_dataframe[column] = result_dataframe[column]/column_entry_count

    return result_dataframe

def display_k_fold_results(path_to_res):
    # display k-fold results
    result_directories = [pos_res for pos_res in os.listdir(path_to_res) if '-' in pos_res]

    # now loop through each group
    total_results = {}
    total_results['training'] = {}
    total_results['separated'] = {}
    completed_groups = []
    for group in result_directories:
        total_results['training'][group] = {}
        total_results['separated'][group] = {}
        # need to load meta data
        with open(path_to_res+group+'/test_results/test_metadata.json') as f:
            meta_data = json.load(f)
        training_list = flatten(list(meta_data['training set'].values()))
        separated_design =  list(meta_data['separated design'].values())[0]
        completed_groups.append(separated_design[0])
        tests = meta_data['tests']

        # now load results for training set
        json_files = select_result_files(path_to_res,group,training_list)
        total_results['training'][group] = process_section_results(json_files,path_to_res+group+'/test_results/')

        # now load results for separate design
        json_files = select_result_files(path_to_res,group,separated_design)
        total_results['separated'][group] = process_section_results(json_files,path_to_res+group+'/test_results/')
    
    # now print results for total training and separated tests
    print('**********************************************************************************************************')
    # training
    recalls_training = []
    parameter_recalls_training = []
    compliance_training = []
    per_relationship_type_list = []
    per_query_type_list = []
    specific_compliance_list = []
    for group_key in total_results['training']:
        recalls_training.append(total_results['training'][group_key]['average recall'])
        parameter_recalls_training.append(total_results['training'][group_key]['average parameter recall'])
        compliance_training.append(total_results['training'][group_key]['compliance test average'])
        specific_compliance_list.append(total_results['training'][group_key]['compliance test results'])
        per_relationship_type_list.append(total_results['training'][group_key]['averages per relationship type'])
        per_query_type_list.append(total_results['training'][group_key]['averages per query type'])
    training_per_relationship_type_average = take_dataframe_average_robust(per_relationship_type_list)
    training_per_query_type_average = take_dataframe_average_robust(per_query_type_list)
    print(training_per_relationship_type_average)
    print(training_per_query_type_average)
    recalls_training = flatten(recalls_training)
    parameter_recalls_training = flatten(parameter_recalls_training)
    if len(recalls_training) != 0:
        print(recalls_training)
        print(f'average training recall: {sum(recalls_training)/len(recalls_training)*100}%')
        print(f'training recall S.D.: {statistics.pstdev(recalls_training)*100}')
    if len(parameter_recalls_training) != 0:
        print(parameter_recalls_training)
        print(f'average parameter training recall: {sum(parameter_recalls_training)/len(parameter_recalls_training)*100}%')
        print(f'training parameter recall S.D.: {statistics.pstdev(parameter_recalls_training)*100}')
    if len(compliance_training) != 0:
        print(compliance_training)
        print(f'average training compliance: {sum(compliance_training)/len(compliance_training)*100}')
        print(f'training compliance S.D.: {statistics.pstdev(compliance_training)*100}')

    # separated
    recalls_separated = []
    parameter_recalls_separated = []
    compliance_separated = []
    per_relationship_type_list = []
    per_query_type_list = []
    for group_key in total_results['separated']:
        recalls_separated.append(total_results['separated'][group_key]['average recall'])
        parameter_recalls_separated.append(total_results['separated'][group_key]['average parameter recall'])
        compliance_separated.append(total_results['separated'][group_key]['compliance test average'])
        per_relationship_type_list.append(total_results['separated'][group_key]['averages per relationship type'])
        per_query_type_list.append(total_results['separated'][group_key]['averages per query type'])
    separated_per_relationship_type_average = take_dataframe_average_robust(per_relationship_type_list)
    separated_per_query_type_average = take_dataframe_average_robust(per_query_type_list)
    print(separated_per_relationship_type_average)
    print(separated_per_query_type_average)
    recalls_separated = flatten(recalls_separated)
    parameter_recalls_separated = flatten(parameter_recalls_separated)
    if len(recalls_separated) != 0:
        print(recalls_separated)
        print(f'average separated recall: {sum(recalls_separated)/len(recalls_separated)*100}%')
        print(f'separated recall S.D.: {statistics.pstdev(recalls_separated)*100}')
    if len(parameter_recalls_separated) != 0:
        print(parameter_recalls_separated)
        print(f'average separated parameter recall: {sum(parameter_recalls_separated)/len(parameter_recalls_separated)*100}%')
        print(f'separated parameter recall S.D.: {statistics.pstdev(parameter_recalls_separated)*100}')
    if len(compliance_separated) != 0:
        print(compliance_separated)
        print(f'average separated compliance: {sum(compliance_separated)/len(compliance_separated)*100}')
        print(f'separated compliance S.D.: {statistics.pstdev(compliance_separated)*100}')
    print(f'completed groups: {completed_groups}')
    return recalls_training, parameter_recalls_training, specific_compliance_list, recalls_separated, parameter_recalls_separated, compliance_separated

def scaling_study():
    # collect performance metrics 
    # collect k-fold results
    recalls_training, parameter_recalls_training, compliance_training, recalls_separated, parameter_recalls_separated, compliance_separated = display_k_fold_results('output_store/complete_k_fold_results/')
    
    # 2023
    json_files,path_to_json = load_current_set('output_store/2023_results/')
    results_2023 = process_section_results(json_files,path_to_json)

    # TRUTHS
    json_files,path_to_json = load_current_set('output_store/ESA_Proj_Results/')
    truths_results = process_section_results(json_files,path_to_json)

    # collect design case scale information
    graph = Graph("bolt://localhost:7687", auth=('neo4j', 'test'))
    database_tools.clear_database(graph)
    # collect k-fold info
    # AVDASI 2013
    mission_name_1 = 'AVDASI_2013'
    #data_extraction.load_mission_requirements(mission_name_1,graph)

    # AVDASI 2013 S1
    design_name_1 = 'AVDASI_2013_S1'
    #design_data = data_extraction.read_data(design_name_1)
    #data_extraction.process_design_data(mission_name_1,design_name_1,design_data,graph)

    # AVDASI 2013 S2
    design_name_2 = 'AVDASI_2013_S2'
    #design_data = data_extraction.read_data(design_name_2)
    #data_extraction.process_design_data(mission_name_1,design_name_2,design_data,graph)
    
    # AVDASI 2017
    mission_name_2 = 'AVDASI_2017'
    #data_extraction.load_mission_requirements(mission_name_2,graph)

    # AVDASI 2017 S1
    design_name_3 = 'AVDASI_2017_S1'
    #design_data = data_extraction.read_data(design_name_3)
    #data_extraction.process_design_data(mission_name_2,design_name_3,design_data,graph)

    # AVDASI 2017 S2
    design_name_4 = 'AVDASI_2017_S2'
    #design_data = data_extraction.read_data(design_name_4)
    #data_extraction.process_design_data(mission_name_2,design_name_4,design_data,graph)

    # AVDASI 2018
    mission_name_3 = 'AVDASI_2018'
    #data_extraction.load_mission_requirements(mission_name_3,graph)

    # AVDASI 2018 S1
    design_name_5 = 'AVDASI_2018_S1'
    #design_data = data_extraction.read_data(design_name_5)
    #data_extraction.process_design_data(mission_name_3,design_name_5,design_data,graph)

    # AVDASI 2018 S2
    design_name_6 = 'AVDASI_2018_S2'
    #design_data = data_extraction.read_data(design_name_6)
    #data_extraction.process_design_data(mission_name_3,design_name_6,design_data,graph)

    # AVDASI 2018 S3
    design_name_7 = 'AVDASI_2018_S3'
    #design_data = data_extraction.read_data(design_name_7)
    #data_extraction.process_design_data(mission_name_3,design_name_7,design_data,graph)

    # AVDASI 2020
    mission_name_4 = 'AVDASI_2020'
    #data_extraction.load_mission_requirements(mission_name_4,graph)

    # AVDASI 2020 S1
    design_name_8 = 'AVDASI_2020_S1'
    #design_data = data_extraction.read_data(design_name_8)
    #data_extraction.process_design_data(mission_name_4,design_name_8,design_data,graph)

    #AVDASI 2020 S2
    design_name_9 = 'AVDASI_2020_S2'
    #design_data = data_extraction.read_data(design_name_9)
    #data_extraction.process_design_data(mission_name_4,design_name_9,design_data,graph)

    #AVDASI 2020 S3
    design_name_10 = 'AVDASI_2020_S3'
    #design_data = data_extraction.read_data(design_name_10)
    #data_extraction.process_design_data(mission_name_4,design_name_10,design_data,graph)

    # AVDASI 2021
    mission_name_5 = 'AVDASI_2021'
    #data_extraction.load_mission_requirements(mission_name_5,graph)
 
    # AVDASI 2021 S1
    design_name_11 = 'AVDASI_2021_S1'
    #design_data = data_extraction.read_data(design_name_11)
    #data_extraction.process_design_data(mission_name_5,design_name_11,design_data,graph)

    # AVDASI 2021 S2
    design_name_12 = 'AVDASI_2021_S2'
    #design_data = data_extraction.read_data(design_name_12)
    #data_extraction.process_design_data(mission_name_5,design_name_12,design_data,graph)

    # AVDASI 2021 S3
    design_name_13 = 'AVDASI_2021_S3'
    #design_data = data_extraction.read_data(design_name_13)
    #data_extraction.process_design_data(mission_name_5,design_name_13,design_data,graph)
    missions ={'AVDASI_2013':[design_name_1,design_name_2],'AVDASI_2017':[design_name_3,design_name_4],'AVDASI_2018':[design_name_5,design_name_6,design_name_7],'AVDASI_2020':[design_name_8,design_name_9,design_name_10],'AVDASI_2021':[design_name_11,design_name_12,design_name_13]}
    database_tools.clear_database(graph)
    load_designs.Load_designs(missions,False)

    no_model_elements_training = []
    no_model_elements_separated = []
    no_requirement_labels_training = []
    no_requirement_labels_separated = []
    no_new_requirement_labels_training = []
    no_new_requirement_labels_separated = []
    for mission_name in tqdm(missions.keys(), colour='green'):
        for design_name_to_remove in missions[mission_name]:
            # reconstruct missions dict order without design to exclude
            requirement_labels_training = set()
            for mission_name_rec in missions.keys():
                for design_name_rec in missions[mission_name_rec]:
                    if design_name_rec != design_name_to_remove:
                        no_model_elements_training.append(return_number_of_elements_in_design(design_name_rec,graph))
                        set_of_requirement_labels = return_set_of_requirement_labels(mission_name_rec,graph)
                        requirement_labels_training.update(set_of_requirement_labels)
                        no_requirement_labels_training.append(len(set_of_requirement_labels))
                        no_new_requirement_labels_training.append(0)
                    else:
                        no_model_elements_separated.append(return_number_of_elements_in_design(design_name_rec,graph))
                        separated_requirement_label_set = return_set_of_requirement_labels(mission_name_rec,graph)
                        no_requirement_labels_separated.append(len(separated_requirement_label_set))
                            
            # now have selected separate design find new requirement labels
            no_new_requirement_labels_separated.append(len(separated_requirement_label_set) - len(requirement_labels_training.intersection(separated_requirement_label_set)))

    print(no_new_requirement_labels_separated)
    print(requirement_labels_training)
    # 2023
    missions = {'AVDASI_2023':['AVDASI_2023_S1','AVDASI_2023_S2','AVDASI_2023_S3']}
    database_tools.clear_database(graph)
    load_designs.Load_designs(missions,False)
    no_model_elements_2023 = []
    no_requirement_labels_2023 = []
    no_new_requirement_labels_2023 = []
    no_model_elements_2023.append(return_number_of_elements_in_design('AVDASI_2023_S1',graph))
    current_label_set = return_set_of_requirement_labels('AVDASI_2023',graph)
    print(current_label_set)
    print(requirement_labels_training)
    no_requirement_labels_2023.append(len(current_label_set))
    no_new_requirement_labels_2023.append(len(current_label_set) - len(requirement_labels_training.intersection(current_label_set)))
    no_model_elements_2023.append(return_number_of_elements_in_design('AVDASI_2023_S2',graph))
    no_requirement_labels_2023.append(len(current_label_set))
    no_new_requirement_labels_2023.append(len(current_label_set) - len(requirement_labels_training.intersection(current_label_set)))
    no_model_elements_2023.append(return_number_of_elements_in_design('AVDASI_2023_S3',graph))
    no_requirement_labels_2023.append(len(current_label_set))
    no_new_requirement_labels_2023.append(len(current_label_set) - len(requirement_labels_training.intersection(current_label_set)))

    # TRUTHS
    missions = {'ESA_Proj':['ESA_Proj_Design']}
    database_tools.clear_database(graph)
    load_designs.Load_designs(missions,False)
    no_model_elements_truths = []
    no_requirement_labels_truths = []
    no_new_requirement_labels_truths = []
    no_model_elements_truths.append(return_number_of_elements_in_design('ESA_Proj_Design',graph))
    current_label_set = return_set_of_requirement_labels('ESA_Proj',graph)
    no_requirement_labels_truths.append(len(current_label_set))
    
    print(current_label_set)
    print(requirement_labels_training)
    no_new_requirement_labels_truths.append(len(current_label_set) - len(requirement_labels_training.intersection(current_label_set)))

    # now to write data to data frame and csv file
    """
    total_results['elements of concern dict'] = elements_of_concern_dict
    total_results['averages per relationship type'] = averages_per_relationship_type
    total_results['average precision'] = average_precision
    total_results['average recall'] = average_recall
    total_results['parameter test results'] = parameter_test_results
    total_results['compliance test average'] =  compliance_test_average
    total_results['parameter elements of concern dict'] = parameter_elements_of_concern_dict
    total_results['average parameter precision'] = average_parameter_precision
    total_results['average parameter recall'] = average_parameter_recall
    """
    # fix compliance training list
    #compliance_train12ing = [1]*(12*13)
    data_dict = {'recalls':recalls_training+recalls_separated+results_2023['average recall']+truths_results['average recall']}
    data_dict['parameter'] = parameter_recalls_training+parameter_recalls_separated+results_2023['average parameter recall']+truths_results['average parameter recall']
    data_dict['compliance'] = flatten(compliance_training)+compliance_separated+results_2023['compliance test results']+truths_results['compliance test results']
    data_dict['no design elements'] = no_model_elements_training+no_model_elements_separated+no_model_elements_2023+no_model_elements_truths
    data_dict['no requirement labels'] = no_requirement_labels_training+no_requirement_labels_separated+no_requirement_labels_2023+no_requirement_labels_truths
    data_dict['no new requirement labels'] = no_new_requirement_labels_training+no_new_requirement_labels_separated+no_new_requirement_labels_2023+no_new_requirement_labels_truths
    results_dataframe = pd.DataFrame(data_dict)
    results_dataframe.to_csv('output_store/scaling.csv')

    return
def return_number_of_elements_in_design(design_name,graph):
    query = """
                MATCH(n:"""+design_name+"""_Design_Instance_Element) RETURN COUNT(n)
            """
    response = database_tools.run_neo_query(['nil'],query,graph)
    for entry in response:
        n = entry['COUNT(n)']
    return n

def return_set_of_requirement_labels(mission_name,graph):
    query = """
                MATCH(n:"""+mission_name+"""_Requirement_Element) RETURN LABELS(n)
            """
    print(query)
    response = database_tools.run_neo_query(['nil'],query,graph)
    labels = []
    for entry in response:
        for label in entry['LABELS(n)']:
            if not 'Requirement_Element' in label and not label == 'Requirement':
                labels.append(label)

    return set(labels)

def main():
    # display current set results
    #json_files,path_to_json = load_current_set()
    #process_section_results(json_files,path_to_json)

    # display k-fold results
    display_k_fold_results('output_store/complete_k_fold_results/')

    # look at all results for scaling trends
    #scaling_study()

if __name__ == '__main__':
    main()
    