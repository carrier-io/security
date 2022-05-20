from typing import Optional, List, ForwardRef
from uuid import uuid4
from pydantic import BaseModel, validator, AnyUrl, parse_obj_as, root_validator

from ..tests import SecurityTestsDAST

from ....shared.models.pd.test_parameters import TestParameter  # todo: workaround for this import


class SecurityTestParamsBase(BaseModel):
    """
    Base case class for security test.
    Used as a parent class for actual security tet model
    """
    _test_params_mapping = {
        'url to scan': 'urls_to_scan',
        'exclusions': 'urls_exclusions',
        'scan location': 'scan_location',
    }
    _required_params = set()

    # the following fields are optional as they are set in test_parameters validator using _test_params_mapping
    urls_to_scan: Optional[List[AnyUrl]] = []
    urls_exclusions: Optional[List[AnyUrl]] = []
    scan_location: Optional[str] = ''

    test_parameters: List[TestParameter]

    @validator('test_parameters')
    def set_values_from_test_params(cls, value, values):
        for i in value:
            if i.name in cls._test_params_mapping.keys():
                values[cls._test_params_mapping[i.name]] = i.default
        return value

    @classmethod
    def from_orm(cls, db_obj: SecurityTestsDAST):
        instance = cls(
            test_parameters=db_obj.test_parameters,
            urls_to_scan=db_obj.urls_to_scan,
            urls_exclusions=[] if db_obj.urls_exclusions == [''] else db_obj.urls_exclusions,
            scan_location=db_obj.scan_location
        )
        return instance

    def update(self, other: ForwardRef('SecurityTestParamsBase')):
        test_params_names = set(map(lambda tp: tp.name, other.test_parameters))
        modified_params = other.test_parameters
        for tp in self.test_parameters:
            if tp.name not in test_params_names:
                modified_params.append(tp)
        self.test_parameters = modified_params
        if other.urls_to_scan:
            self.urls_to_scan = other.urls_to_scan
        if other.urls_exclusions and other.urls_exclusions != ['']:
            self.urls_exclusions = other.urls_exclusions
        if other.scan_location:
            self.scan_location = other.scan_location


SecurityTestParamsBase.update_forward_refs()


_required_params = {'url to scan', }


class SecurityTestParam(TestParameter):
    """
    Each ROW of test_params table
    """
    _type_mapping_by_name = {'url to scan': List[AnyUrl]}
    _required_params = _required_params

    @validator('default')
    def validate_required(cls, value, values):
        if values['name'] in cls._required_params:
            assert value and value != [''], f'{values["name"]} is required'
        return value


class SecurityTestParamsCommon(SecurityTestParamsBase):
    """
    Whole test_params table
    """
    _required_params = _required_params
    test_parameters: List[SecurityTestParam]

    @validator('test_parameters')
    def required_test_param(cls, value):
        lacking_values = cls._required_params.difference(set(i.name for i in value))
        assert not lacking_values, f'The following parameters are required: {" ".join(lacking_values)}'
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
