from sqlalchemy.sql import func, LABEL_STYLE_TABLENAME_PLUS_COL

from .models.api_tests import SecurityTestsDAST
from .models.pd.security_test import SecurityTestParamsCommon, SecurityTestCommon, SecurityTestParams
from .models.security_reports import SecurityReport
from .models.security_results import SecurityResultsDAST
from .utils import run_test

from ..shared.utils.rpc import RpcMixin


def security_results_or_404(run_id: int) -> SecurityResultsDAST:
    return SecurityResultsDAST.query.get_or_404(run_id)


def overview_data(project_id: int) -> dict:
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


def parse_test_parameters(data: list, **kwargs) -> dict:
    pd_object = SecurityTestParamsCommon(test_parameters=data)
    return pd_object.dict(**kwargs)


def parse_common_test_parameters(project_id: int, name: str, description: str, **kwargs) -> dict:
    rpc = RpcMixin().rpc
    project = rpc.call.project_get_or_404(project_id=project_id)
    pd_object = SecurityTestCommon(
        project_id=project.id,
        project_name=project.name,
        name=name,
        description=description
    )
    return pd_object.dict(**kwargs)


def run_scheduled_test(test_id: int, test_params: list):
    test = SecurityTestsDAST.query.filter(SecurityTestsDAST.id == test_id).one()
    test_params_schedule_pd = SecurityTestParams(test_parameters=test_params)
    test_params_existing_pd = SecurityTestParams.from_orm(test)
    test_params_existing_pd.update(test_params_schedule_pd)
    test.__dict__.update(test_params_existing_pd.dict())
    return run_test(test)
