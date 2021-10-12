from ...projects.models.statistics import Statistic
from ...tasks.api.utils import run_task


def exec_test(project_id, event):
    response = run_task(project_id, event)
    response["redirect"] = f"/task/{response['task_id']}/results"

    statistic = Statistic.query.filter_by(project_id=project_id).first()
    statistic.dast_scans += 1
    statistic.commit()

    return response


def format_test_parameters(test_parameters: list) -> dict:
    result = dict()
    # print('TP', test_parameters)
    # print('TP', type(test_parameters))
    # import json
    # print('TP', json.loads(test_parameters.replace("'", '"')))
    # print('TP', type(json.loads(test_parameters.replace("'", '"'))))
    for i in test_parameters:
        # print('III', i)
        name = i.pop('name').lower()
        # data = dict()
        # for k, v in i.items():
        #     if not k.startswith('_'):
        #         data[k] = v
        result[name] = i['default']
    return result
