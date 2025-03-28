import spacy
import nalmage.diagram_generation
import sysml
import pprint

log_filename = 'transcript.txt'

def identify_named_elements(completion):
    NER = spacy.load("en_core_web_sm")
    promt_text = NER(completion)
    for word in promt_text.ents:
        logged_print((word.text,word.label_))

def identify_bulleted_list(completion):
    checked_chars = {'-','•',','}
    # identifying bullet character
    counts = []
    for char in checked_chars:
        counts.append(completion.count(char))

    bullet_char = list(checked_chars)[counts.index(max(counts))]
    elements =  remove_illegal_chars(completion).replace(bullet_char,'').split('\n')
    # remove empty entries
    elements = list(filter(None, elements))
    return {'elements':elements,'selected_bullet_type':char}

def remove_illegal_chars(str):
    # removing illegal chars
    checked_chars = {'[',']','"',"'",'{','}','.','(',')',',','/','\\'}
    for char in checked_chars:
        str = str.replace(char,'')
    
    #converting spaces to _
    str = str.replace(' ','_')
    return str

def identify_element_detail(element_text):
    checked_chars = {'-',':'}
    # identifying explanation character
    counts = []
    for char in checked_chars:
        counts.append(element_text.count(char))
    explanation_char = list(checked_chars)[counts.index(max(counts))]
    element = {'element':element_text,'text':'none given','children':[]}
    if explanation_char in element_text:
            element =  {'element':element_text.split(explanation_char,1)[0],'text':element_text.split(explanation_char,1)[1],'children':[]}
    return element

def identify_formatted_elements(element_text):
    element_text_splits = element_text.split(':')
    if len(element_text_splits) == 2:
        element = {'element':remove_illegal_chars(element_text_splits[0]),'traceable/interfaced type':remove_illegal_chars(element_text_splits[1])}
    else:
        logged_print(f'WARNING: LLM output formatting error for {element_text}')
        element = {'element':remove_illegal_chars(element_text_splits[0]),'traceable/interfaced type':'NONE_PROVIDED_FORMAT_ERROR'}
    return element

def output_model_to_yaml(model,model_file_name):
    model.to_yaml(model_file_name)
    nalmage.diagram_generation.create_plantuml_diagram(model_file_name)
    logged_print(f'model outline diagram updated, file name: tool_integration/{model_file_name}')

def import_model_from_yaml(model_file_name):
    model = sysml.read_yaml(model_file_name)
    nalmage.diagram_generation.create_plantuml_diagram(model_file_name)
    logged_print(f'model outline diagram updated, file name: tool_integration/{model_file_name}')
    return model

def logged_print(text):
    text = str(text)
    print(text)
    with open(log_filename, "a",encoding="utf-8") as text_file:
        text_file.write(text)

def plogged_print(text):
    text = str(text)
    pprint.pprint(text)
    with open(log_filename, "a",encoding="utf-8") as text_file:
        text_file.write(text)