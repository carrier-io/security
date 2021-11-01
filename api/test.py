from json import loads

from flask_restful import abort
from sqlalchemy import and_

from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser

from ..models.api_tests import SecurityTestsDAST
from ..models.security_results import SecurityResultsDAST
from ..models.security_reports import SecurityReport
from .utils import exec_test, format_test_parameters, ValidationError


class SecurityTestApi(RestResource):
    _post_rules = (
        dict(name="test_name", type=str, required=False, location='json'),
    )

    _put_rules = (
        dict(name="name", type=str, location='json'),
        dict(name="description", type=str, location='json'),
        dict(name="parameters", type=str, location='json'),
        dict(name="integrations", type=str, location='json'),
        dict(name="processing", type=str, location='json'),
        dict(name="run_test", type=bool, location='json'),
    )

    def __init__(self):
        super(SecurityTestApi, self).__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self.post_parser = build_req_parser(rules=self._post_rules)
        self.put_parser = build_req_parser(rules=self._put_rules)

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

    def put(self, project_id, test_id):
        """ Update test data """
        args = self.put_parser.parse_args(strict=False)
        print('EDIT ARGS', args)
        run_test = args.pop("run_test")

        errors = []

        test_name = args.get('name', None)
        if not test_name:
            errors.append({
                'field': 'name',
                'feedback': 'Test name is required'
            })

        try:
            test_parameters = format_test_parameters(loads(args['parameters'].replace("'", '"')))
        except ValidationError as e:
            errors.append({
                'field': 'parameters',
                'feedback': e.data
            })

        if errors:
            return abort(400, data=errors)

        urls_to_scan = [test_parameters.pop('url to scan').get('default')]
        urls_exclusions = test_parameters.pop('exclusions').get('default', [])
        scan_location = test_parameters.pop('scan location').get('default', '')

        integrations = loads(args['integrations'].replace("'", '"'))
        processing = loads(args['processing'].replace("'", '"'))

        update_values = {
            "name": test_name,
            'description': args['description'],
            "urls_to_scan": urls_to_scan,
            "urls_exclusions": urls_exclusions,
            'scan_location': scan_location,
            'test_parameters': test_parameters.values(),
            'integrations': integrations,
            "processing": processing
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
        print('GOT TEST', test)
        if run_test:
            security_results = SecurityResultsDAST(
                project_id=project.id,
                test_id=test.id,
                test_uid=test.test_uid,
                test_name=test.name
            )
            security_results.insert()

            event = []
            test.results_test_id = security_results.id
            test.commit()
            event.append(test.configure_execution_json("cc"))

            response = exec_test(project.id, event)

            return response

        return {"message": "Parameters for test were updated"}

    def post(self, project_id, test_id):
        """ Run test """
        args = self.post_parser.parse_args(strict=False)
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

        event = list()

        security_results = SecurityResultsDAST(
            project_id=project.id,
            test_id=test.id,
            test_uid=test.test_uid,
            test_name=args["test_name"],
            test_config=test.to_json()
        )
        security_results.insert()

        test.results_test_id = security_results.id
        test.commit()

        event.append(test.configure_execution_json("cc"))

        if args.get("type") == "config":
            return event[0]

        response = exec_test(project.id, event)
        return response
