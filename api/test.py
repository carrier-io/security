import json
from queue import Empty
from typing import Union

from flask import request, make_response
from flask_restful import abort, Resource
from pylon.core.tools import log
from sqlalchemy import and_
from pydantic import ValidationError

from ..utils import run_test, ValidationErrorPD

from ..models.api_tests import SecurityTestsDAST
from ..models.security_results import SecurityResultsDAST
from ..models.security_reports import SecurityReport
# from .utils import format_test_parameters, ValidationError

from ...shared.utils.rpc import RpcMixin


class SecurityTestApi(Resource, RpcMixin):

    @staticmethod
    def get_filter(project_id: int, test_id: Union[int, str]):
        if isinstance(test_id, int):
            return and_(
                SecurityTestsDAST.project_id == project_id,
                SecurityTestsDAST.id == test_id
            )
        return and_(
            SecurityTestsDAST.project_id == project_id,
            SecurityTestsDAST.test_uid == test_id
        )

    def get(self, project_id: int, test_id: Union[int, str]):
        test = SecurityResultsDAST.query.filter(self.get_filter(project_id, test_id)).first()
        test = test.to_json()
        scanners = SecurityReport.query.with_entities(SecurityReport.tool_name).filter(
            self.get_filter(project_id, test_id)
        ).distinct().all()

        if scanners:
            test["scanners"] = ", ".join([scan[0] for scan in scanners])
        return test

    def put(self, project_id: int, test_id: Union[int, str]):
        """ Update test data """
        errors = list()

        run_test_ = request.json.pop('run_test', False)
        test_name = request.json.pop('name', None)
        test_description = request.json.pop('description', None)

        try:
            test_data = self.rpc.call.security_test_create_common_parameters(
                project_id=project_id,
                name=test_name,
                description=test_description,
                exclude={'test_uid', }
            )
        except ValidationError as e:
            test_data = dict()
            print('test_data_error 1', e)
            errors.extend(e.errors())

        for i, v in request.json.items():
            try:
                print(f'security test create :: parsing :: [{i}]')
                test_data.update(self.rpc.call_function_with_timeout(
                    func=f'security_test_create_{i}',
                    timeout=1,
                    data=v,
                ))
            except Empty:
                print(f'Cannot find parser for {i}')
                # errors.append(ValidationErrorPD('alert_bar', f'Cannot find parser for {i}'))
                # return make_response(ValidationErrorPD('alert_bar', f'Cannot find parser for {i}').json(), 404)
            except ValidationError as e:
                errors.extend(e.errors())

        if errors:
            return make_response(json.dumps(errors), 400)

        # update_values = {
        #     'name': test_name,
        #     'description': request.json['description'],
        #     'urls_to_scan': urls_to_scan,
        #     'urls_exclusions': urls_exclusions,
        #     'scan_location': scan_location,
        #     'test_parameters': test_parameters.values(),
        #     'integrations': integrations,
        # }

        # project = self.rpc.call.project_get_or_404(project_id=project_id)

        test = SecurityTestsDAST.query.filter(self.get_filter(project_id, test_id))
        test.update(test_data)
        SecurityTestsDAST.commit()

        # log.warning('self.get_filter(project_id, test_id)')
        # log.warning([project_id, test_id])
        # log.warning(self.get_filter(project_id, test_id))

        test = test.first()
        # log.warning('test')
        # log.warning(test)
        # log.warning(SecurityTestsDAST.query.filter(and_(
        #     SecurityTestsDAST.project_id == project_id,
        #     SecurityTestsDAST.test_uid == test_id
        # )).first())
        if run_test_:
            return run_test(test)

        return make_response(test.to_json(), 200)

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = SecurityTestsDAST.query.filter(
            self.get_filter(project_id, test_id)
        ).first()
        return run_test(test, config_only=request.json.get('type', False))
