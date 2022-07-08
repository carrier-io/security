from typing import Optional, List
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator

from ....shared.models.pd.test_parameters import TestParameter, TestParamsBase  # todo: workaround for this import


_required_params = {'url to scan', }


class SecurityTestParam(TestParameter):
    """
    Each ROW of test_params table
    """
    _type_mapping_by_name = {
        'url to scan': List[AnyUrl],
        'exclusions': List[Optional[AnyUrl]]
    }

    _required_params = _required_params


class SecurityTestParams(TestParamsBase):
    """
    Base case class for security test.
    Used as a parent class for actual security test model
    """
    _required_params = _required_params

    # the following fields are optional as they are set in validator using _test_params_mapping
    urls_to_scan: Optional[List[AnyUrl]] = []
    urls_exclusions: Optional[List[Optional[AnyUrl]]] = []
    scan_location: Optional[str] = ''
    test_parameters: List[SecurityTestParam]

    @validator('scan_location', 'urls_exclusions', 'urls_to_scan', always=True)
    def set_values_from_test_params(cls, value, values, field):
        if value and value != field.default:
            return value
        _test_params_mapping = {
            'url to scan': 'urls_to_scan',
            'urls_to_scan': 'url to scan',
            'exclusions': 'urls_exclusions',
            'urls_exclusions': 'exclusions',
            'scan location': 'scan_location',
            'scan_location': 'scan location',
        }

        mapped_name = _test_params_mapping.get(field.name)
        if mapped_name:
            try:
                return [i.default for i in values['test_parameters'] if i.name == mapped_name][0]
            except (IndexError, KeyError):
                ...

        return value


class SecurityTestCommon(BaseModel):
    """
    Model of test itself without test_params or other plugin module's data
    """
    # _empty_str_to_none = empty_str_to_none
    project_id: int
    project_name: str
    test_uid: Optional[str]
    name: str
    description: Optional[str] = ''

    @root_validator
    def set_uuid(cls, values):
        if not values.get('test_uid'):
            values['test_uid'] = str(uuid4())
        return values

    @root_validator(pre=True, allow_reuse=True)
    def empty_str_to_none(cls, values):
        removed = []
        for k in list(values.keys()):
            if values[k] == '':
                removed.append(k)
                del values[k]
        return values
