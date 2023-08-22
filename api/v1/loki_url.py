import json
import gzip

import flask
from flask import make_response
from flask_restful import Resource
from pylon.core.tools import log
from pylon.core.seeds.minio import MinIOHelper
from tools import auth
from tools import LokiLogFetcher

from ...models.results import SecurityResultsDAST


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["security.app.reports.view"],
    })
    def get(self, project_id: int):
        # key = flask.request.args.get("task_id", None)
        result_key = flask.request.args.get("result_test_id", None)
        if not result_key:  # or key not in state:
            return make_response({"message": ""}, 404)

        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        websocket_base_url = LokiLogFetcher.from_project(project).get_websocket_url(project)

        # TODO: probably need to rename params
        # logs_query = "{" + f'task_key="{key}"' + "}"
        # logs_query = "{" + f'task_key="{key}"&result_test_id="{result_key}"&project_id="{project_id}"' + "}"
        # logs_query = "{" + f'task_key="{key}",result_test_id="{result_key}",project_id="{project_id}"' + "}"

        build_id = SecurityResultsDAST.query.get_or_404(result_key).build_id
        logs_query = "{" + f'report_id="{result_key}",project="{project_id}",build_id="{build_id}"' + "}"

        # TODO: Uncomment or re-write when all settings will be ready
        # state = self._get_task_state()
        # logs_start = state[key].get("ts_start", 0)
        logs_start = 0
        logs_limit = 10000000000

        return make_response(
            {
                "websocket_url": f"{websocket_base_url}?query={logs_query}&start={logs_start}&limit={logs_limit}"},
            200
        )

    # def _get_minio(self):  # pylint: disable=R0201
    #     return MinIOHelper.get_client(self.app_setting["storage"])  # todo: what is app_setting??
    #
    # def _load_state_object(self, bucket, key):
    #     minio = self._get_minio()
    #     try:
    #         return json.loads(gzip.decompress(minio.get_object(bucket, key).read()))
    #     except:  # pylint: disable=W0702
    #         log.exception("Failed to load state object")
    #         return None
    #
    # def _get_task_state(self):
    #     state = self._load_state_object(
    #         self.module.settings["storage"]["buckets"]["state"],
    #         self.module.settings["storage"]["objects"]["task_state"]
    #     )
    #     return state if state is not None else dict()
