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
        test_data = rpc.call.security_test_create_common_parameters(
            project_id=project_id,
            name=test_name,
            description=test_description,
            **common_kwargs
        )
    except ValidationError as e:
        # print('test_data_error 1', e)
        test_data = dict()
        errors.extend(e.errors())
        if raise_immediately:
            return test_data, errors

    for k, v in request_data.items():
        try:
            # print(f'security test create :: parsing :: [{k}]')
            test_data.update(rpc.call_function_with_timeout(
                func=f'security_test_create_{k}',
                timeout=1,
                data=v,
                **test_create_rpc_kwargs
            ))
        except Empty:
            log.warning(f'Cannot find parser for {k}')
            if skip_validation_if_undefined:
                test_data.update({k: v})
            # errors.append(ValidationErrorPD('alert_bar', f'Cannot find parser for {i}'))
            # return make_response(ValidationErrorPD('alert_bar', f'Cannot find parser for {i}').json(), 404)
        except ValidationError as e:
            # err_list = e.errors()
            # for i in err_list:
            #     log.warning('QQQ')
            #     log.warning(type(i))
            #     log.warning(i)
            #     i['loc'] = [k, *i['loc']]
            # errors.extend(err_list)

            for i in e.errors():
                # log.warning('QQQ')
                # log.warning(type(i))
                # log.warning(i)
                i['loc'] = [k, *i['loc']]
            # log.warning('YYY')
            # log.warning(e.errors())
            errors.extend(e.errors())

            if raise_immediately:
                return test_data, errors
        except Exception as e:
            # log.warning('Exception as e')
            # log.warning(type(e))
            e.loc = [k, *getattr(e, 'loc', [])]
            errors.append(ValidationErrorPD(e.loc, str(e)))
            if raise_immediately:
                return test_data, errors

    return test_data, errors



