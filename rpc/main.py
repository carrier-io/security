from sqlalchemy.sql import func, LABEL_STYLE_TABLENAME_PLUS_COL

from ..models.tests import SecurityTestsDAST
# from ..models.pd.security_test import SecurityTestParamsCommon, SecurityTestCommon, SecurityTestParamsBase
from ..models.pd.security_test import SecurityTestParams, SecurityTestCommon
from ..models.reports import SecurityReport
from ..models.results import SecurityResultsDAST
from ..utils import run_test

from tools import rpc_tools

from pylon.core.tools import web
from pydantic import ValidationError


class RPC:
    @web.rpc('security_results_or_404', 'results_or_404')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def results_or_404(self, run_id: int) -> SecurityResultsDAST:
        return SecurityResultsDAST.query.get_or_404(run_id)

    @web.rpc('security_overview_data', 'overview_data')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def overview_data(self, project_id: int) -> dict:
        queries = [
            func.sum(getattr(SecurityResultsDAST, i)).label(f'sum_{i}')
            for i in SecurityReport.SEVERITY_CHOICES.keys()
        ]
        q = SecurityResultsDAST.query.with_entities(
            *queries
        ).filter(
            SecurityResultsDAST.project_id == project_id,
        )
        return dict(zip([i['name'] for i in q.column_descriptions], q.first()))

    @web.rpc('security_test_create_test_parameters', 'parse_test_parameters')
    # @rpc_tools.wrap_exceptions(RuntimeError)
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_test_parameters(self, data: list, **kwargs) -> dict:
        pd_object = SecurityTestParams(test_parameters=data)
        return pd_object.dict(**kwargs)

    @web.rpc('security_test_create_common_parameters', 'parse_common_test_parameters')
    # @rpc_tools.wrap_exceptions(RuntimeError)
    @rpc_tools.wrap_exceptions(ValidationError)
    def parse_common_test_parameters(self, project_id: int, name: str, description: str, **kwargs) -> dict:
        project = self.context.rpc_manager.call.project_get_or_404(project_id=project_id)
        pd_object = SecurityTestCommon(
            project_id=project.id,
            project_name=project.name,
            name=name,
            description=description
        )
        return pd_object.dict(**kwargs)

    @web.rpc('security_run_scheduled_test', 'run_scheduled_test')
    @rpc_tools.wrap_exceptions(RuntimeError)
    def run_scheduled_test(self, test_id: int, test_params: list) -> dict:
        test = SecurityTestsDAST.query.filter(SecurityTestsDAST.id == test_id).one()
        test_params_schedule_pd = SecurityTestParams(test_parameters=test_params)
        test_params_existing_pd = SecurityTestParams.from_orm(test)
        test_params_existing_pd.update(test_params_schedule_pd)
        test.__dict__.update(test_params_existing_pd.dict())
        return run_test(test)
