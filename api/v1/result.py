from flask_restful import Resource

from ...models.security_results import SecurityResultsDAST


class API(Resource):
    url_params = [
        '<int:project_id>/<int:result_id>',
    ]

    def __init__(self, module):
        self.module = module

    def get(self, project_id: int, result_id: int):
        obj = SecurityResultsDAST.query.filter(
            SecurityResultsDAST.project_id == project_id,
            SecurityResultsDAST.id == result_id,
        ).one()
        return obj.to_json(), 200
