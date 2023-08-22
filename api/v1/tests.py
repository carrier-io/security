from queue import Empty

from flask_restful import Resource
from pylon.core.tools import log
from flask import request
from sqlalchemy import and_

from ...models.tests import SecurityTestsDAST
from ...utils import parse_test_data, run_test

from tools import api_tools, auth


class API(Resource):
    url_params = [
        '<int:project_id>',
    ]

    def __init__(self, module):
        self.module = module

    @auth.decorators.check_api({
        "permissions": ["security.app.tests.view"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": True},
        }
    })
    def get(self, project_id: int):
        total, res = api_tools.get(project_id, request.args, SecurityTestsDAST)
        rows = []
        for i in res:
            test = i.to_json()
            schedules = test.pop('schedules', [])
            if schedules:
                try:
                    test['scheduling'] = self.module.context.rpc_manager.timeout(
                        2).scheduling_security_load_from_db_by_ids(schedules)
                except Empty:
                    ...
            test['scanners'] = i.scanners
            rows.append(test)
        return {"total": total, "rows": rows}, 200

    @staticmethod
    def get_schedules_ids(filter_) -> set:
        r = set()
        for i in SecurityTestsDAST.query.with_entities(SecurityTestsDAST.schedules).filter(
                filter_
        ).all():
            r.update(set(*i))
        return r

    @auth.decorators.check_api({
        "permissions": ["security.app.tests.delete"],
        "recommended_roles": {
            "default": {"admin": True, "editor": False, "viewer": False},
        }
    })
    def delete(self, project_id: int):
        project = self.module.context.rpc_manager.call.project_get_or_404(
            project_id=project_id)
        try:
            delete_ids = list(map(int, request.args["id[]"].split(',')))
        except TypeError:
            return 'IDs must be integers', 400

        filter_ = and_(
            SecurityTestsDAST.project_id == project.id,
            SecurityTestsDAST.id.in_(delete_ids)
        )

        try:
            self.module.context.rpc_manager.timeout(3).scheduling_delete_schedules(
                self.get_schedules_ids(filter_)
            )
        except Empty:
            ...

        SecurityTestsDAST.query.filter(
            filter_
        ).delete()
        SecurityTestsDAST.commit()

        return {'ids': delete_ids}, 200

    @auth.decorators.check_api({
        "permissions": ["security.app.tests.create"],
        "recommended_roles": {
            "default": {"admin": True, "editor": True, "viewer": False},
        }
    })
    def post(self, project_id: int):
        """
        Post method for creating and running test
        """

        run_test_ = request.json.pop('run_test', False)
        test_data, errors = parse_test_data(
            project_id=project_id,
            request_data=request.json,
            rpc=self.module.context.rpc_manager,
        )

        if errors:
            return errors, 400
            # return make_response(json.dumps(errors, default=lambda o: o.dict()), 400)

        # log.warning('TEST DATA')
        # log.warning(test_data)

        schedules = test_data.pop('scheduling', [])
        # log.warning('schedules')
        # log.warning(schedules)

        test = SecurityTestsDAST(**test_data)
        test.insert()

        # for s in schedules:
        #     log.warning('!!!adding schedule')
        #     log.warning(s)
        #     test.add_schedule(s, commit_immediately=False)
        # test.commit()
        test.handle_change_schedules(schedules)

        if run_test_:
            resp = run_test(test)
            return resp, resp.get('code', 200)
        return test.to_json()
