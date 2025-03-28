import design_problem_formulation.design_problem_query_tools as design_problem_query_tools

def test_edge_justification_against_framework(edge,variability_framework,graph):
    root_type = edge[0]
    relationship_type = edge[1]
    target_type = edge[2]
    mission_name = ''
    design_name = ''

    design_query = {'query type':'Requirement to Function SA','requirement':['3'],'design variable':['SHIRE'],'dependant variable':[],'additional model elements':[]}
    completed_query = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,design_name,graph)
    result = False
    return {'result':result,'edge':edge}

def justify_design_against_framework(variability_framework,mission_name,design_name,graph):
    design_query = {'query type':'Function to Component SA','requirement':['MIS_001','MIS_002','MIS_003','MIS_004','MIS_005','MIS_006','MIS_007','MIS_008','MIS_009','MIS_010','MIS_011','MIS_012','MIS_013','MIS_014','MIS_015','MIS_016'],'design variable':['SHIRE'],'dependant variable':[],'additional model elements':[]}
    completed_query = design_problem_query_tools.design_context_query(variability_framework,design_query,mission_name,design_name,graph)
