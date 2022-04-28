import json
from typing import Union, List

from flask import request, make_response
from flask_restful import abort, Resource
from pylon.core.tools import log
from sqlalchemy import and_

from ..utils import run_test, parse_test_data
from ..models.api_tests import SecurityTestsDAST
# from ..models.security_results import SecurityResultsDAST
# from ..models.security_reports import SecurityReport

from ...shared.utils.rpc import RpcMixin


class SecurityTestApi(Resource, RpcMixin):
    def get(self, project_id: int, test_id: Union[int, str]):
        log.warning('SecurityTestApi GET CALLED')
        # test = SecurityResultsDAST.query.filter(SecurityResultsDAST(project_id, test_id)).first()
        # test = test.to_json()

        return make_response(None, 204)

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

        test = SecurityTestsDAST.query.filter(SecurityTestsDAST.get_api_filter(project_id, test_id))

        schedules = test_data.pop('scheduling', [])
        # log.warning('schedules')
        # log.warning(schedules)

        # test = SecurityTestsDAST(**test_data)
        # test.insert()
        #

        test.update(test_data)
        SecurityTestsDAST.commit()
        test = test.one()

        # for s in schedules:
        #     log.warning('!!!adding schedule')
        #     log.warning(s)
        #     test.add_schedule(s, commit_immediately=False)
        # test.commit()
        test.handle_change_schedules(schedules)


        # test = test.first()
        if run_test_:
            return run_test(test)

        return make_response(test.to_json(), 200)

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = SecurityTestsDAST.query.filter(
            SecurityTestsDAST.get_api_filter(project_id, test_id)
        ).first()
        return run_test(test, config_only=request.json.get('type', False))



