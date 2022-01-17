from typing import Optional, Dict, Any, List, Union, get_origin
from uuid import uuid4

from pydantic import BaseModel, Json, validator, AnyUrl, parse_obj_as, root_validator, ValidationError

from ..api_tests import SecurityTestsDAST


def test_param_model_factory(required_params: Union[list, set, tuple] = None, type_mapping_by_name: dict = None):
    class TestParameter(BaseModel):
        class Config:
            anystr_strip_whitespace = True
            anystr_lower = True

        _type_mapping = {
            'url': List[AnyUrl],
            'urls': List[AnyUrl],
            'string': str,
            'number': int,
            'list': list,
            'item': str
        }

        # _empty_str_to_none = empty_str_to_none

        name: str
        type: Optional[str] = 'string'
        description: Optional[str] = ''
        default: Optional[Any] = ''

        # @validator('name', allow_reuse=True, always=True)
        # def validate_required(cls, value):
        #     assert value, f'{value} is required'
        #     return

        @validator('default', allow_reuse=True, always=True)
        def validate_required_value(cls, value, values):
            # print('default validator', values)
            name = values.get('name')

            type_ = values.get('type', str)
            if cls._type_mapping_by_name.get(name):
                type_ = cls._type_mapping_by_name.get(name)
            elif cls._type_mapping.get(type_):
                type_ = cls._type_mapping.get(type_)

            # print('default validator types', type_)
            if name in cls._required_params:
                # print('required!!', value, values.get('default'))
                assert value, f'{name} is required'
            value = cls.convert_types(value, type_)
            # print('\tvalue final', parse_obj_as(Optional[type_], value))
            return parse_obj_as(Optional[type_], value)

        @staticmethod
        def convert_types(value, _type, list_delimiter=','):
            _checked_type = get_origin(_type) or _type
            # print('\tvalue', value, type(value))
            # print('\ttype', _type, _checked_type)
            if value is not None:
                if isinstance(value, str):
                    value = value.strip()
                if not isinstance(value, list) and _checked_type is list:
                    value = [i.strip() for i in str(value).split(list_delimiter)]
                elif isinstance(value, list) and _checked_type is not list:
                    value = list_delimiter.join(value)
            # print('\tvalue AFTER', value)
            return value

    TestParameter._required_params = set() if not required_params else set((i.lower() for i in required_params))
    TestParameter._type_mapping_by_name = type_mapping_by_name or dict()
    return TestParameter


@root_validator(pre=True, allow_reuse=True)
def empty_str_to_none(cls, values):
    removed = []
    for k in list(values.keys()):
        if values[k] == '':
            removed.append(k)
            del values[k]
    return values


class SecurityTestParams(BaseModel):
    _test_params_mapping = {
        'url to scan': 'urls_to_scan',
        'exclusions': 'urls_exclusions',
        'scan location': 'scan_location',
    }

    # the following fields are optional as they are set in test_parameters validator using _test_params_mapping
    urls_to_scan: Optional[List[AnyUrl]] = []
    urls_exclusions: Optional[List[AnyUrl]] = []
    scan_location: Optional[str] = ''

    test_parameters: List[test_param_model_factory(type_mapping_by_name={'url to scan': List[AnyUrl]})]

    @validator('test_parameters')
    def set_values_from_test_params(cls, value, values):
        from pylon.core.tools import log
        log.info('validator test_parameters called')
        for i in value:
            # print('i', i)
            # print('i in', i.name in cls._test_params_mapping.keys())
            if i.name in cls._test_params_mapping.keys():
                values[cls._test_params_mapping[i.name]] = i.default
        return value

    @classmethod
    def from_orm(cls, db_obj: SecurityTestsDAST):
        # from pylon.core.tools import log
        # log.info(f'FROM ORM {dict(test_parameters=db_obj.test_parameters,urls_to_scan=db_obj.urls_to_scan,urls_exclusions=[] if db_obj.urls_exclusions == [""] else db_obj.urls_exclusions,scan_location=db_obj.scan_location)}')
        instance = cls(
            test_parameters=db_obj.test_parameters,
            urls_to_scan=db_obj.urls_to_scan,
            urls_exclusions=[] if db_obj.urls_exclusions == [''] else db_obj.urls_exclusions,
            scan_location=db_obj.scan_location
        )
        # instance = cls(**db_obj.__dict__)
        return instance

    def update(self, other: 'SecurityTestParams'):
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


class SecurityTestParamsCommon(SecurityTestParams):
    test_parameters: List[
        test_param_model_factory(
            required_params=['url to scan'],
            type_mapping_by_name={'url to scan': List[AnyUrl]}
        )
    ]


class SecurityTestCommon(BaseModel):
    _empty_str_to_none = empty_str_to_none

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
