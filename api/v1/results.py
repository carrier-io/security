from flask import make_response, request
from flask_restful import Resource

from tools import api_tools

from ...models.security_results import SecurityResultsDAST


class API(Resource):
    def __init__(self, module):
        self.module = module

    def get(self, project_id: int):
        args = request.args
        reports = []
        total, res = api_tools.get(project_id, args, SecurityResultsDAST)
        for each in res:
            reports.append(each.to_json())
        return make_response({"total": total, "rows": reports}, 200)
