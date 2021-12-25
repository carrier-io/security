from queue import Empty

from flask_restful import Resource
from pylon.core.tools import log
from sqlalchemy import and_
from flask import request, make_response
from pydantic import ValidationError

from ..rpc import security_results_or_404
from ..utils import run_test, ValidationErrorPD
from ..models.api_tests import SecurityTestsDAST
from ..models.security_thresholds import SecurityThresholds

from ...shared.utils.rpc import RpcMixin
from ...shared.utils.api_utils import get


class SecurityTestsApi(Resource, RpcMixin):
    def get(self, project_id: int):
        reports = []
        total, res = get(project_id, request.args, SecurityTestsDAST)
        for each in res:
            reports.append(each.to_json())
        return {"total": total, "rows": reports}

    def delete(self, project_id: int):
        project = self.rpc.call.project_get_or_404(project_id=project_id)
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
        # test_name = request.json.get('name', None)
        # if not test_name:
        #     errors.append({
        #         'field': 'name',
        #         'feedback': 'Test name is required'
        #     })

        # project = self.rpc.project_get_or_404(project_id=project_id)
        try:
            test_run = request.json.pop('run_test')
        except KeyError:
            test_run = False

        test_name = None
        test_description = None
        test_data = dict()

        try:
            test_name = request.json.pop('name')
        except KeyError:
            ...
        try:
            test_description = request.json.pop('description')
        except KeyError:
            ...

        try:
            test_data = self.rpc.call.security_test_create_common_parameters(
                project_id=project_id,
                name=test_name,
                description=test_description
            )
        except ValidationError as e:
            print('test_data_error 1')
            print(e)
            errors.extend(e.errors())
            # return make_response(e.json(), 400)

        print('test_data 1')
        print(test_data)

        # for i in set(request.json.keys()):
        for i, v in request.json.items():
            try:
                print('security test create :: parsing :: [%s]', i)
                test_data.update(self.rpc.call_function_with_timeout(
                    func='{prefix}_{key}'.format(
                        prefix='security_test_create',
                        key=i
                    ),
                    timeout=3,
                    data=v,
                ))
            except Empty:
                print('Cannot find parser for %s', i)

                # return make_response(ValidationErrorPD('alert_bar', f'Cannot find parser for {i}').json(), 404)
            except ValidationError as e:
                errors.extend(e.errors())
                # return make_response(e.json(), 400)
            print('test_data 2')
            print(test_data)

        print('test_data 3 FINAL')
        print(test_data)

        # try:
        #     test_parameters = format_test_parameters(request.json['test_parameters'])
        #
        # except ValidationError as e:
        #     errors.append({
        #         'field': 'test_parameters',
        #         'feedback': e.data
        #     })
        #
        # if errors:
        #     return abort(400, data=errors)
        #
        # urls_to_scan = [test_parameters.pop('url to scan').get('default')]
        # urls_exclusions = test_parameters.pop('exclusions').get('default', [])
        # scan_location = test_parameters.pop('scan location').get('default', '')

        integrations = request.json['integrations']

        # test = SecurityTestsDAST(
        #     project_id=project.id,
        #     project_name=project.name,
        #     test_uid=str(uuid4()),
        #     name=test_name,
        #     description=request.json['description'],
        #
        #     urls_to_scan=urls_to_scan,
        #     urls_exclusions=urls_exclusions,
        #     scan_location=scan_location,
        #     test_parameters=test_parameters.values(),
        #
        #     integrations=integrations,
        # )


        if errors:
            import json
            return make_response(json.dumps(errors), 400)

        test = SecurityTestsDAST(**test_data, integrations=integrations, )
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

        if run_test:
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
