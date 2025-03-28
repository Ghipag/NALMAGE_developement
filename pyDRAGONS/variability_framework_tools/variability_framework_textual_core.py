import database_interaction.data_extraction as data_extraction
class Rules:
    """
    A class for parsing and applying rules in a rule-based system.

    Attributes:
        alias_list (list): A list of type aliases.
        prohibition_list (list): A list of prohibited relationships.
        permission_list (list): A list of permitted relationships.
        exclusive_list (list): A list of exclusive relationships.

    Methods:
        parse_rules(rules, framework_module):
            Parse and store rules.

        add_relevant_inverse(relationship, framework_module, obj, second, rule_list):
            Add relevant inverse relationships to the rule list.

        resolve_types_inner(types, aliases):
            Recursively resolve types based on aliases.

        resolve_types(thing):
            Resolve types for a given object.

        allowed(action_to_test):
            Check if an action is allowed based on rules.
    """
    alias_list = []
    prohibition_list = []
    permission_list = []
    exclusive_list = []

    def parse_rules(rules,framework_module):
        """
        Parse and store rules.

        Args:
            rules (list): List of rule strings.
            framework_module: The framework module to identify relationships.

        Returns:
            None
        """
        for rule in rules:
            if ' is ' in rule:
                type, alias = rule.split(' is ')
                Rules.alias_list.append((type, alias))
            elif ' may only ' in rule:
                obj, rest = rule.split(' may only have relationship of type ')
                relationship,with_clause, second = rest.split(' ')
                Rules.exclusive_list.append((obj, relationship, second))
                Rules.exclusive_list = Rules.add_relevant_inverse(relationship,framework_module,obj,second,Rules.exclusive_list)
            elif ' may not ' in rule:
                obj, rest = rule.split(' may not have relationship of type ')
                relationship,with_clause, second = rest.split(' ')
                Rules.prohibition_list.append((obj, relationship, second))
                Rules.prohibition_list = Rules.add_relevant_inverse(relationship,framework_module,obj,second,Rules.prohibition_list)
            elif ' may ' in rule:
                obj, rest = rule.split(' may have relationship of type ')
                relationship,with_clause, second = rest.split(' ')
                Rules.permission_list.append((obj, relationship, second))
                Rules.permission_list = Rules.add_relevant_inverse(relationship,framework_module,obj,second,Rules.permission_list)

    def add_relevant_inverse(relationship,framework_module,obj,second,rule_list):
        """
        Parse and store rules.

        Args:
            rules (list): List of rule strings.
            framework_module: The framework module to identify relationships.

        Returns:
            None
        """
        # check for relationship inverse
        relationship_class = identify_relationship_class_from_name(relationship,framework_module)
        # generating test instance and finding inverse
        relationship_inverse = relationship_class('foo','bar').inverse
        if relationship_inverse is not None:
            relationship_inverse_class = identify_relationship_class(relationship_inverse,framework_module)
            relationship_inverse_tag = relationship_inverse_class('foo','bar').name
            rule_list.append((second, relationship_inverse_tag, obj))
        return rule_list

    def resolve_types_inner(types, aliases):
        """
        Parse and store rules.

        Args:
            rules (list): List of rule strings.
            framework_module: The framework module to identify relationships.

        Returns:
            None
        """
        for (source_type, alias_type) in aliases[:]:
            if source_type in types:
                types.add(alias_type)
                aliases.remove((source_type, alias_type))
                return Rules.resolve_types_inner(types, aliases)
        return types

    def resolve_types(thing):
        """
        Parse and store rules.

        Args:
            rules (list): List of rule strings.
            framework_module: The framework module to identify relationships.

        Returns:
            None
        """
        types = set(thing.type)
        return Rules.resolve_types_inner(types, Rules.alias_list[:])

    def allowed(action_to_test):
        """
        Check if an action is allowed based on rules.

        Args:
            action_to_test: The action to test.

        Returns:
            bool: True if the action is allowed, False otherwise.
        """
        a_types = Rules.resolve_types(action_to_test.a)
        b_types = Rules.resolve_types(action_to_test.b)

        for (a, action, b) in Rules.exclusive_list:
            if action == action_to_test.name:
                if a in a_types and b in b_types:
                    print ('-- allowed by exclusive_list')
                    return True

        for (a, action, b) in Rules.prohibition_list:
            if action == action_to_test.name:
                if a in a_types and b in b_types:
                    print ('-- forbidden')
                    return False

        for (a, action, b) in Rules.permission_list:
            if action == action_to_test.name:
                if a in a_types and b in b_types:
                    if not action in (x for (a2,x,b2) in Rules.exclusive_list if x == action and a2 in a_types):
                        print ('-- allowed')
                        return True
                    else:
                        print ('-- forbidden by exclusive_list')
                        return False

        print ('-- no rules match')

class Relationship:
    def __init__(self, name, a, b, inverse = None):
        self.name = name
        self.a = a
        self.b = b
        self.inverse = inverse

    def invoke(self):
        print('You feel a strange sensation...')

    def forbidden(self):
        print(f"{self.a.name} has been linked via {self.name} to {self.b.name}, but that is not possible")

    def __call__(self):
        if Rules.allowed(self):
            self.invoke()
            success_flag = True
        else:
            self.forbidden()
            success_flag = False
        print('----------')
        return success_flag
class Thing:
    def __init__(self, name, *type):
        self.name = name
        self.type = ['Thing', *type]

    def relationship(self, relationship_class, *args):
        return relationship_class(self, *args)()
    
def load_classifier_rules(data,rules,classifier_type):
    rules.append(f'{classifier_type} is Design_Element')
    data = data_extraction.generate_uid(data,'ontology/')

    input_data = data[['uid','name']]
    #drop empty entries
    input_data =  input_data.dropna()
    # Convert data frame to list of dictionaries
    input_data = list(input_data.T.to_dict().values())#
    for entry in input_data:
        # now add the current definition in the ontology
        rules.append(f'{entry["name"]} is {classifier_type}')

def identify_relationship_class_from_name(relationship_tag,framework_module):
    relationship_name = relationship_tag.title().replace('_','')
    class_handle = getattr(framework_module, relationship_name)
    return class_handle

def identify_relationship_class(relationship_tag,framework_module):
    relationship_name = relationship_tag
    class_handle = getattr(framework_module, relationship_name)
    return class_handle