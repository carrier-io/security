from typing import Union
from sqlalchemy.sql import func, LABEL_STYLE_TABLENAME_PLUS_COL

from .api.test import SecurityTestApi
from .models.api_tests import SecurityTestsDAST
from .models.pd.security_test import SecurityTestParamsCommon, SecurityTestCommon, test_param_model_factory, \
    SecurityTestParams
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


def rpc_test_param_model_factory(required_params: Union[list, set, tuple] = None, type_mapping_by_name: dict = None):
    return test_param_model_factory(required_params, type_mapping_by_name)


def run_scheduled_test(test_id: int, test_params: list):
    test = SecurityTestsDAST.query.filter(SecurityTestsDAST.id == test_id).one()
    # from pylon.core.tools import log
    # log.info(f'RUNNING test {test_id} == {test.id}')
    # log.info(f'RUNNING test {test.test_parameters}')
    test_params_schedule_pd = SecurityTestParams(test_parameters=test_params)
    # log.info(f'RUNNING test PD test_params_schedule_pd: {test_params_schedule_pd}')
    test_params_existing_pd = SecurityTestParams.from_orm(test)
    # log.info(f'RUNNING test PD test_params_existing_pd: {test_params_existing_pd}')

    # test_params_names = set(map(lambda tp: tp['name'], test_params))
    #
    # modified_params = test_params
    # for tp in test.test_parameters:
    #     if tp['name'] not in test_params_names:
    #         modified_params.append(tp)
    test_params_existing_pd.update(test_params_schedule_pd)
    # log.info(f'R modified_params {test_params_existing_pd}')
    # log.info(f'R modified_params {test_params_existing_pd.dict()}')
    test.__dict__.update(test_params_existing_pd.dict())

    # test.urls_to_scan = modified_params.pop('url_to_scan', test.urls_to_scan)
    # test.urls_to_scan = modified_params.pop('urls_to_scan', test.urls_to_scan)
    # test.urls_exclusions = modified_params.pop('urls_exclusions', test.urls_exclusions)
    # test.scan_location = modified_params.pop('scan_location', test.scan_location)
    # test.test_parameters = modified_params

    # log.info(f'R modified_test {test}')
    return run_test(test)
