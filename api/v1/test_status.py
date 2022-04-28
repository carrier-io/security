from datetime import datetime
from io import BytesIO
from urllib.parse import urlunparse, urlparse

import requests
from flask import current_app, request, make_response
from flask_restful import Resource
from pylon.core.tools import log
from sqlalchemy import and_, func

from ...models.security_results import SecurityResultsDAST
# from ...models.security_reports import SecurityReport


class API(Resource):
    def __init__(self, module):
        self.module = module

    def put(self, project_id: int, test_id: int):
        args = request.json
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

        return make_response({"message": f"Status for test_id={test_id} of project_id: {project_id} updated"}, 200)


def write_test_run_logs_to_minio_bucket(test: SecurityResultsDAST, file_name='log.txt'):
    loki_settings_url = urlparse(current_app.config["CONTEXT"].settings.get('loki', {}).get('url'))  # todo: check if self.module.context.config returns the same
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

            file_output.write(f'Test {test.test_name} (id={test.test_id}) run log:\n'.encode(enc))

            unpacked_values = []
            for i in results['data']['result']:
                for ii in i['values']:
                    ii.append(i['stream']['level'])
                    unpacked_values.append(ii)
            for unix_ns, log_line, level in sorted(unpacked_values, key=lambda x: int(x[0])):
                timestamp = datetime.fromtimestamp(int(unix_ns) / 1e9).strftime("%Y-%m-%d %H:%M:%S")
                file_output.write(
                    f'{timestamp}\t{level}\t{log_line}\n'.encode(enc)
                )
            minio_client = test.get_minio_client()
            file_output.seek(0)
            minio_client.upload_file(test.bucket_name, file_output, file_name)
        else:
            log.warning('Request to loki failed with status %s', response.status_code)
