from flask import request
from flask_restful import abort
from sqlalchemy import and_

from ..utils import run_test
from ...shared.utils.restApi import RestResource

from ..models.api_tests import SecurityTestsDAST
from ..models.security_results import SecurityResultsDAST
from ..models.security_reports import SecurityReport
# from .utils import format_test_parameters, ValidationError


class SecurityTestApi(RestResource):
    def get(self, project_id, test_id):
        project = self.rpc.project_get_or_404(project_id=project_id)

        if isinstance(test_id, int):
            _filter = and_(
                SecurityResultsDAST.project_id == project.id, SecurityResultsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityResultsDAST.project_id == project.id, SecurityResultsDAST.test_uid == test_id
            )
        test = SecurityResultsDAST.query.filter(_filter).first()
        test = test.to_json()
        scanners = SecurityReport.query.with_entities(SecurityReport.tool_name).filter(
            and_(
                SecurityReport.project_id == project.id,
                SecurityReport.report_id == test_id
            )
        ).distinct().all()

        if scanners:
            test["scanners"] = ", ".join([scan[0] for scan in scanners])
        return test

    def put(self, project_id: int, test_id: int):
        """ Update test data """
        run_test = request.json.get('run_test', False)

        errors = []

        test_name = request.json.get('name', None)
        if not test_name:
            errors.append({
                'field': 'name',
                'feedback': 'Test name is required'
            })

        try:
            test_parameters = format_test_parameters(request.json['test_parameters'])
        except ValidationError as e:
            errors.append({
                'field': 'test_parameters',
                'feedback': e.data
            })

        if errors:
            return abort(400, data=errors)

        # urls_to_scan = [test_parameters.pop('url to scan').get('default')]
        # urls_exclusions = test_parameters.pop('exclusions').get('default', [])
        # scan_location = test_parameters.pop('scan location').get('default', '')

        integrations = request.json['integrations']

        update_values = {
            'name': test_name,
            'description': request.json['description'],
            'urls_to_scan': urls_to_scan,
            'urls_exclusions': urls_exclusions,
            'scan_location': scan_location,
            'test_parameters': test_parameters.values(),
            'integrations': integrations,
        }

        project = self.rpc.project_get_or_404(project_id=project_id)

        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
        test = SecurityTestsDAST.query.filter(_filter)

        test.update(update_values)
        SecurityTestsDAST.commit()

        test = test.first()
        if run_test:
            # security_results = SecurityResultsDAST(
            #     project_id=project.id,
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
            # response = exec_test(project.id, event)
            # response['result_id'] = security_results.id
            # return response
            return run_test(test)

        return {"message": "Parameters for test were updated"}

    def post(self, project_id, test_id):
        """ Run test """
        project = self.rpc.project_get_or_404(project_id=project_id)

        if isinstance(test_id, int):
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityTestsDAST.project_id == project.id, SecurityTestsDAST.test_uid == test_id
            )
        test = SecurityTestsDAST.query.filter(_filter).first()

        # event = list()
        #
        # security_results = SecurityResultsDAST(
        #     project_id=project.id,
        #     test_id=test.id,
        #     test_uid=test.test_uid,
        #     test_name=request.json["test_name"],
        # )
        # security_results.insert()
        #
        # test.results_test_id = security_results.id
        # test.commit()
        #
        # event.append(test.configure_execution_json("cc"))
        #
        # if request.json.get("type") == "config":
        #     return event[0]
        #
        # response = exec_test(project.id, event)
        # response['result_id'] = security_results.id
        return run_test(test, config_only=request.json.get('type', False))
