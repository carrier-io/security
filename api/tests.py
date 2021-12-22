from uuid import uuid4

from flask_restful import abort
from sqlalchemy import and_
from flask import request

from ..rpc import security_results_or_404
from ..utils import run_test
from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import get

from ..models.api_tests import SecurityTestsDAST
from ..models.security_thresholds import SecurityThresholds
from .utils import format_test_parameters, ValidationError


class SecurityTestsApi(RestResource):
    def get(self, project_id: int):
        reports = []
        total, res = get(project_id, request.args, SecurityTestsDAST)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def delete(self, project_id: int):
        project = self.rpc.project_get_or_404(project_id=project_id)
        # query_result = SecurityTestsDAST.query.filter(
        #     and_(SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id.in_(request.json["id[]"]))
        # ).all()
        # for each in query_result:
        #     each.delete()
        SecurityTestsDAST.query.filter(
            and_(SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id.in_(request.json["id[]"]))
        ).delete(synchronize_session=False)
        return {"message": "deleted"}

    def post(self, project_id: int):
        """
        Post method for creating and running test
        """

        errors = []
        test_name = request.json.get('name', None)
        if not test_name:
            errors.append({
                'field': 'name',
                'feedback': 'Test name is required'
            })

        project = self.rpc.project_get_or_404(project_id=project_id)

        try:
            test_parameters = format_test_parameters(request.json['test_parameters'])

        except ValidationError as e:
            errors.append({
                'field': 'test_parameters',
                'feedback': e.data
            })

        if errors:
            return abort(400, data=errors)

        urls_to_scan = [test_parameters.pop('url to scan').get('default')]
        urls_exclusions = test_parameters.pop('exclusions').get('default', [])
        scan_location = test_parameters.pop('scan location').get('default', '')

        integrations = request.json['integrations']

        test_uid = str(uuid4())
        test = SecurityTestsDAST(
            project_id=project.id,
            project_name=project.name,
            test_uid=test_uid,
            name=test_name,
            description=request.json['description'],
            urls_to_scan=urls_to_scan,
            urls_exclusions=urls_exclusions,
            scan_location=scan_location,
            test_parameters=test_parameters.values(),
            integrations=integrations,
        )
        test.insert()

        threshold = SecurityThresholds(
            project_id=project.id,
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

        if request.json.get('run_test', False):
            # security_results = SecurityResultsDAST(
            #     project_id=project.id,
            #     test_id=test.id,
            #     test_uid=test_uid,
            #     test_name=test.name
            # )
            # security_results.insert()
            #
            # event = []
            # test.results_test_id = security_results.id
            # test.commit()
            # event.append(test.configure_execution_json("cc"))
            #
            # response = exec_test(project.id, event)
            # response['result_id'] = security_results.id
            # return response
            return run_test(test)
        return test.to_json()


class SecurityTestsRerun(RestResource):
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

        # security_results = SecurityResultsDAST(
        #     project_id=test.project_id,
        #     test_id=test.id,
        #     test_uid=test.test_uid,
        #     test_name=test.name
        # )
        # security_results.insert()
        #
        # event = []
        # test.results_test_id = security_results.id
        # test.commit()
        # event.append(test.configure_execution_json("cc"))
        #
        # response = exec_test(test_config['project_id'], event)
        # response['result_id'] = security_results.id
        # return response
        return run_test(test)

