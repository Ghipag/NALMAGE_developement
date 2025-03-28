def generate_prompt(design_query):
    match design_query['query type']:
        case 'Requirement to Function SA':
            prompt_string = f'Suggest the main functions (worded as functions), listing them with "-" bullet points, performed by an Earth observation satellite given the following requirements: (list requirements)'
        case 'Function to Component SA':
            des_string = ''
            for entry_key in design_query['design variable'].keys():
                des_string = des_string + entry_key + ', '
            des_string = des_string[0:-2]
            dep_string = ''
            for entry_key in design_query['dependant variable'].keys():
                dep_string = dep_string + entry_key + ', '
            dep_string = dep_string[0:-2]
            prompt_string =f'Group the following functions into modes used by the {des_string}: {dep_string}, listing the modes with "-" bullet points'
    expected_output_types = design_query['additional model elements']
    return prompt_string,expected_output_types