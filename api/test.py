import json
from typing import Union

from flask import request, make_response
from flask_restful import abort, Resource
from sqlalchemy import and_

from ..utils import run_test, parse_test_data
from ..models.api_tests import SecurityTestsDAST
from ..models.security_results import SecurityResultsDAST
from ..models.security_reports import SecurityReport

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
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.rpc,
            common_kwargs={'exclude': {'test_uid', }}
        )

        if errors:
            return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)

        test = SecurityTestsDAST.query.filter(self.get_filter(project_id, test_id))
        test.update(test_data)
        SecurityTestsDAST.commit()

        test = test.first()
        if run_test_:
            return run_test(test)

        return make_response(test.to_json(), 200)

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = SecurityTestsDAST.query.filter(
            self.get_filter(project_id, test_id)
        ).first()
        return run_test(test, config_only=request.json.get('type', False))
