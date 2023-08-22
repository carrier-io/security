from flask import request
from flask_restful import Resource
from sqlalchemy import and_

from ...models.tests import SecurityTestsDAST


class API(Resource):
    url_params = [
        '<int:project_id>/<string:name>/<string:scope>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, name: str, scope: str):
        project = self.module.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        query_result = SecurityTestsDAST.query.with_entities(SecurityTestsDAST.test_uid).filter(
            SecurityTestsDAST.name == name,
            SecurityTestsDAST.project_id == project.id,
            SecurityTestsDAST.description == scope,
        ).first()
        return query_result[0], 200
