import json

from .models.api_tests import SecurityTestsDAST
from .models.security_results import SecurityResultsDAST

from ..tasks.api.utils import run_task
from ..projects.models.statistics import Statistic


def run_test(test: SecurityTestsDAST, config_only=False):
    security_results = SecurityResultsDAST(
        project_id=test.project_id,
        test_id=test.id,
        test_uid=test.test_uid,
        test_name=test.name
    )
    security_results.insert()

    event = []
    test.results_test_id = security_results.id
    test.commit()
    event.append(test.configure_execution_json("cc"))

    if config_only:
        return event[0]

    response = run_task(test.project_id, event)
    response['redirect'] = f'/task/{response["task_id"]}/results'

    statistic = Statistic.query.filter_by(project_id=test.project_id).first()
    statistic.dast_scans += 1
    statistic.commit()

    response['result_id'] = security_results.id
    return response


class ValidationErrorPD(Exception):
    def __init__(self, loc: str, msg: str):
        self.loc = loc
        self.msg = msg
        super().__init__({'loc': [loc], 'msg': msg})

    def json(self):
        return json.dumps(self.dict())

    def dict(self):
        return {'loc': [self.loc], 'msg': self.msg}
