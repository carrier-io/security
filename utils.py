import json
from queue import Empty
from typing import Tuple, Union
from sqlalchemy import and_
from pydantic import ValidationError

from pylon.core.tools import log

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
    def __init__(self, loc: Union[str, list], msg: str):
        self.loc = [loc] if isinstance(loc, str) else loc
        self.msg = msg
        super().__init__({'loc': self.loc, 'msg': msg})

    def json(self):
        return json.dumps(self.dict())

    def dict(self):
        return {'loc': self.loc, 'msg': self.msg}


def parse_test_data(project_id: int, request_data: dict, *,
                    rpc=None, common_kwargs: dict = None,
                    test_create_rpc_kwargs: dict = None,
                    raise_immediately: bool = False,
                    skip_validation_if_undefined: bool = True,
                    ) -> Tuple[dict, list]:
    if not rpc:
        from ..shared.utils.rpc import RpcMixin
        rpc = RpcMixin().rpc

    common_kwargs = common_kwargs or dict()
    test_create_rpc_kwargs = test_create_rpc_kwargs or dict()

    errors = list()

    test_name = request_data.pop('name', None)
    test_description = request_data.pop('description', None)

    try:
        from .rpc import parse_common_test_parameters
        test_data = parse_common_test_parameters(
            project_id=project_id,
            name=test_name,
            description=test_description,
            **common_kwargs
        )
    except ValidationError as e:
        test_data = dict()
        errors.extend(e.errors())
        if raise_immediately:
            return test_data, errors

    for k, v in request_data.items():
        try:
            # log.info(f'security test create :: parsing :: [{k}]')
            test_data.update(rpc.call_function_with_timeout(
                func=f'security_test_create_{k}',
                timeout=2,
                data=v,
                **test_create_rpc_kwargs
            ))
        except Empty:
            log.warning(f'Cannot find parser for {k}')
            if skip_validation_if_undefined:
                test_data.update({k: v})
        except ValidationError as e:
            for i in e.errors():
                i['loc'] = [k, *i['loc']]
            errors.extend(e.errors())

            if raise_immediately:
                return test_data, errors
        except Exception as e:
            log.warning(f'Exception as e {type(e)}')
            e.loc = [k, *getattr(e, 'loc', [])]
            errors.append(ValidationErrorPD(e.loc, str(e)))
            if raise_immediately:
                return test_data, errors

    return test_data, errors



