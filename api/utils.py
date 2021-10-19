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
    # print('TP', test_parameters)
    result = dict()
    item_value_key = 'default'
    for i in test_parameters:
        # print('i[item_value_key]', type(i[item_value_key]), i[item_value_key])
        name = i.get('name').lower()

        for k in set(i.keys()):
            if k.startswith('_'):
                del i[k]

        data_type = i.get('type', '').lower()
        if data_type == 'list':
            if not isinstance(i[item_value_key], list):
                i[item_value_key] = [x.strip() for x in i[item_value_key].split(',')]
        elif data_type in ('integer', 'number'):
            i[item_value_key] = float(i[item_value_key])
        elif data_type in ('string', ''):
            if isinstance(i[item_value_key], list):
                i[item_value_key] = ','.join(i[item_value_key])
            i[item_value_key] = i[item_value_key].strip()

        result[name] = i
    # print('AND RESULT IS', result)
    return result
