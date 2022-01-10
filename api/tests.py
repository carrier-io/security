import json

from flask_restful import Resource
from sqlalchemy import and_
from flask import request, make_response

from ..rpc import security_results_or_404
from ..utils import run_test, parse_test_data
from ..models.api_tests import SecurityTestsDAST
from ..models.security_thresholds import SecurityThresholds

from ...shared.utils.rpc import RpcMixin
from ...shared.utils.api_utils import get


class SecurityTestsApi(Resource, RpcMixin):
    def get(self, project_id: int):
        total, res = get(project_id, request.args, SecurityTestsDAST)

        return make_response(
            {"total": total, "rows": [i.to_json() for i in res]},
            200
        )

    def delete(self, project_id: int):
        project = self.rpc.call.project_get_or_404(project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return make_response('IDs must be integers', 400)

        SecurityTestsDAST.query.filter(
            and_(
                SecurityTestsDAST.project_id == project.id,
                SecurityTestsDAST.id.in_(delete_ids)
            )
        ).delete()
        SecurityTestsDAST.commit()
        return make_response({'ids': delete_ids}, 200)

    def post(self, project_id: int):
        """
        Post method for creating and running test
        """

        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.rpc,
        )

        if errors:
            return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)

        test = SecurityTestsDAST(**test_data)
        test.insert()

        threshold = SecurityThresholds(
            project_id=test.project_id,
            test_name=test.name,
            test_uid=test.test_uid,
            critical=-1,
            high=-1,
            medium=-1,
            low=-1,
            info=-1,
            critical_life=-1,
            high_life=-1,
            medium_life=-1,
            low_life=-1,
            info_life=-1
        )
        threshold.insert()

        if run_test_:
            return run_test(test)
        return test.to_json()


class SecurityTestsRerun(Resource):
    def post(self, security_results_dast_id: int):
        """
        Post method for re-running test
        """

        test_result = security_results_or_404(security_results_dast_id)
        test_config = test_result.test_config

        test = SecurityTestsDAST.query.get(test_config['id'])
        if not test:
            test = SecurityTestsDAST(
                project_id=test_config['project_id'],
                project_name=test_config['project_name'],
                test_uid=test_config['test_uid'],
                name=test_config['name'],
                description=test_config['description'],

                urls_to_scan=test_config['urls_to_scan'],
                urls_exclusions=test_config['urls_exclusions'],
                scan_location=test_config['scan_location'],
                test_parameters=test_config['test_parameters'],

                integrations=test_config['integrations'],
            )
            test.insert()

        return run_test(test)
