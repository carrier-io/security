import json
from typing import Union

from flask import request, make_response
from flask_restful import Resource
from pylon.core.tools import log

from ...utils import run_test, parse_test_data
from ...models.api_tests import SecurityTestsDAST


class API(Resource):
    url_params = [
        '<int:project_id>/<int:test_id>',
        '<int:project_id>/<string:test_id>',
    ]

    def __init__(self, module):
        self.module = module

    # def get(self, project_id: int, test_id: Union[int, str]):
    #     log.warning('SecurityTestApi GET CALLED')
    #     # test = SecurityResultsDAST.query.filter(SecurityResultsDAST(project_id, test_id)).first()
    #     # test = test.to_json()
    #     return make_response(None, 204)

    def put(self, project_id: int, test_id: Union[int, str]):
        """ Update test data """
        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
            common_kwargs={'exclude': {'test_uid', }}
        )

        if errors:
            return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)

        test_query = SecurityTestsDAST.query.filter(SecurityTestsDAST.get_api_filter(project_id, test_id))

        schedules = test_data.pop('scheduling', [])

        test_query.update(test_data)
        SecurityTestsDAST.commit()
        test = test_query.one()

        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return make_response(resp, resp.get('code', 200))

        return make_response(test.to_json(), 200)

    def post(self, project_id: int, test_id: Union[int, str]):
        """ Run test """
        test = SecurityTestsDAST.query.filter(
            SecurityTestsDAST.get_api_filter(project_id, test_id)
        ).first()
        resp = run_test(test, config_only=request.json.get('type', False))
        return make_response(resp, resp.get('code', 200))
