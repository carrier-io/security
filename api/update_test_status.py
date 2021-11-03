from io import BytesIO
from urllib.parse import urlunparse, urlparse

import requests
from flask import current_app
from sqlalchemy import and_, func

from ...shared.utils.restApi import RestResource
from ...shared.utils.api_utils import build_req_parser
from ..models.security_results import SecurityResultsDAST
from ..models.security_reports import SecurityReport


class TestStatusUpdater(RestResource):
    _put_rules = (
        dict(name="test_status", type=dict, location="json"),
    )

    def __init__(self):
        super().__init__()
        self.__init_req_parsers()

    def __init_req_parsers(self):
        self._parser_put = build_req_parser(rules=self._put_rules)

    def put(self, project_id: int, test_id: int):
        args = self._parser_put.parse_args(strict=False)
        test_status = args.get("test_status")

        if not test_status:
            return {"message": "There's not enough parameters"}, 400

        if isinstance(test_id, int):
            _filter = and_(
                SecurityResultsDAST.project_id == project_id, SecurityResultsDAST.id == test_id
            )
        else:
            _filter = and_(
                SecurityResultsDAST.project_id == project_id, SecurityResultsDAST.test_uid == test_id
            )
        test = SecurityResultsDAST.query.filter(_filter).first()
        test.set_test_status(test_status)

        if test_status['status'].lower().startswith('finished'):
            test.update_severity_counts()
            test.update_status_counts()
            test.update_findings_counts()
            test.commit()

            write_test_run_logs_to_minio_bucket(test)

        return {"message": f"Status for test_id={test_id} of project_id: {project_id} updated"}, 200


def write_test_run_logs_to_minio_bucket(test, file_name='log.txt'):
    loki_settings_url = urlparse(current_app.config["CONTEXT"].settings.get('loki', {}).get('url'))
    if loki_settings_url:
        #
        task_key = test.test_id
        result_key = test.id
        project_id = test.project_id
        #
        logs_query = "{" + f'task_key="{task_key}",result_test_id="{result_key}",project_id="{project_id}"' + "}"
        #
        loki_url = urlunparse((
            loki_settings_url.scheme,
            loki_settings_url.netloc,
            '/loki/api/v1/query_range',
            None,
            'query=' + logs_query,
            None
        ))
        response = requests.get(loki_url)
        if response.ok:
            results = response.json()
            enc = 'utf-8'
            file_output = BytesIO()

            file_output.write(f'Test run {test.test_id} log:\n'.encode(enc))
            for i in results['data']['result']:
                for timestamp, log_line in i['values']:
                    file_output.write(f'{timestamp}\t{log_line}\n'.encode(enc))
            minio_client = test.get_minio_client()
            file_output.seek(0)
            minio_client.upload_file(test.bucket_name, file_output, file_name)
