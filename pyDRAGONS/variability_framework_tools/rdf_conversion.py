import os
from tqdm import tqdm

def convert_to_rdf_class_orientated(rules,rdf_file_name):
    # writing to two rdf files - one with confidence data included, one without for visualization
    with open(rdf_file_name+'.ttl', "w") as rdf_file:
        with open(rdf_file_name+'_viz.ttl', "w") as rdf_viz_file:
            rdf_file.write('@prefix : <http://dig.isi.edu/> .\n')
            rdf_viz_file.write('@prefix : <http://dig.isi.edu/> .\n')

            for rule in tqdm(rules, colour = 'green'):
                # need to cycle through type definitions first and then collect other related rules for each type             
                if ' is ' in rule:
                    type_name = rule.split(' is')[0]
                    parent_name = rule.split('is ')[1]
                    rdf_file.write(f'\n:{type_name} a :{parent_name} ;\n')

                    # now find related rules
                    rule_index = 0 
                    while rule_index < len(rules):
                        related_rule = rules[rule_index]
                        if 'may' in related_rule and related_rule.split(' ')[0] == type_name:
                            #rdf_file.write(';\n')

                            # extract data
                            relationship_name = related_rule.split('relationship of type ')[1].split(' with')[0]
                            second_type = related_rule.split('with ')[1].split(',confidence: ')[0]

                            # write data to file(s)
                            rdf_file.write(f'   :{relationship_name} :{second_type} ;\n')

                        if rule_index == len(rules)-1:
                            rdf_file.write(' .\n')

                        rule_index += 1

        rdf_file.close()
    #print('generating graphics')
    #os.system(f'python ontology-visualisation/ontology_viz.py -o {rdf_file_name}.dot {rdf_file_name}.ttl')
    #os.system(f'dot -Tsvg -o {rdf_file_name}.svg {rdf_file_name}.dot')
                    
def convert_to_rdf_relationship_orientated(rules,rdf_file_name):
    # writing to two rdf files - one with confidence data included, one without for visualization
    with open(rdf_file_name+'.ttl', "w") as rdf_file:
        rdf_file.write('@prefix : <http://dig.isi.edu/> .\n')

        for rule in rules:
            # need to cycle through type definitions first and then collect other related rules for each type             
            if ' is ' in rule:
                type_name = rule.split(' is')[0]
                parent_name = rule.split('is ')[1]

                rdf_file.write(f'\n:{type_name} a :{parent_name}  .\n')

                # now find related rules
                rule_index = 0 
                while rule_index < len(rules):
                    related_rule = rules[rule_index]
                    # property rules
                    if ' must be ' in related_rule and related_rule.split(' ')[0] == type_name:
                        constraint_spec = related_rule.split(' must be ')[1]
                        rdf_file.write(f'\n:{type_name} :has_constraint :{constraint_spec}  .\n')

                    # relationship rules
                    if 'may' in related_rule and related_rule.split(' ')[0] == type_name:

                        # extract data
                        relationship_name = related_rule.split('relationship of type ')[1].split(' with')[0]
                        second_type = related_rule.split('with ')[1].split(',confidence: ')[0]
                        confidence = related_rule.split(',confidence: ')[1].split(',lift')[0]
                        lift = related_rule.split(',lift: ')[1].split(',support')[0]
                        support = related_rule.split(',support: ')[1]

                        # write data to file(s)
                        rdf_file.write(f':{type_name}_{relationship_name}_{second_type} a :{relationship_name}  ;\n')
                        rdf_file.write(f'   :{relationship_name} :{type_name} ;\n')
                        rdf_file.write(f'   :{relationship_name} :{second_type} ;\n')
                        rdf_file.write(f'   :confidence  {confidence} ;\n')
                        rdf_file.write(f'   :lift  {lift} ;\n')
                        rdf_file.write(f'   :support  {support} .\n')

                    rule_index += 1

        rdf_file.close()
    os.system(f'python ontology-visualisation/ontology_viz.py -o {rdf_file_name}.dot {rdf_file_name}.ttl')
    os.system(f'dot -Tsvg -o {rdf_file_name}.svg {rdf_file_name}.dot')