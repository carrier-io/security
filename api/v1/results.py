from flask import make_response, request
from flask_restful import Resource

from tools import api_tools, auth

from ...models.results import SecurityResultsDAST


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["security.app.reports.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int):
        args = request.args
        reports = []
        total, res = api_tools.get(project_id, args, SecurityResultsDAST)
        for each in res:
            reports.append(each.to_json())
        return make_response({"total": total, "rows": reports}, 200)
