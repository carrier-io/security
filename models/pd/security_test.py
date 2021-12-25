from abc import ABC
from typing import Optional, Dict, Any, List, Union, get_origin
from uuid import uuid4

from pydantic import BaseModel, Json, validator, AnyUrl, parse_obj_as, root_validator, ValidationError


@root_validator(pre=True, allow_reuse=True)
def empty_str_to_none(cls, values):
    removed = []
    # print('\nROOT', values)
    for k in list(values.keys()):
        if values[k] == '':
            removed.append(k)
            del values[k]
            # values[k] = None
    # print('\tROOT removed', removed)
    return values


def test_param_model_factory(required_params: Union[list, set, tuple] = None):
    class TestParameter(BaseModel):
        class Config:
            anystr_strip_whitespace = True
            anystr_lower = True

        _type_mapping = {
            'url': List[AnyUrl],
            'urls': List[AnyUrl],
            'string': str,
            'number': int,
            'list': list
        }

        _empty_str_to_none = empty_str_to_none
        
        name: str
        type: Optional[str] = 'string'
        description: Optional[str]
        default: Optional[Any] = None

        # @validator('name', allow_reuse=True, always=True)
        # def validate_required(cls, value):
        #     assert value, f'{value} is required'
        #     return

        @validator('default', allow_reuse=True, always=True)
        def validate_required_value(cls, value, values):
            # print('default validator', values)
            name = values.get('name')
            type_ = values.get('type')
            if name in cls._required_params:
                # print('required!!', value, values.get('default'))
                assert value, f'{name} is required'
            value = cls.convert_types(value, cls._type_mapping.get(type_, str))
            # print('\tvalue final', parse_obj_as(Optional[cls._type_mapping.get(type_, str)], value))
            return parse_obj_as(Optional[cls._type_mapping.get(type_, str)], value)

        

        @staticmethod
        def convert_types(value, _type, list_delimiter=','):
            _checked_type = get_origin(_type) or _type
            # print('\tvalue', value)
            # print('\ttype', _type, _checked_type)
            if value:
                if isinstance(value, str):
                    value = value.strip()
                if not isinstance(value, list) and _checked_type == list:
                    value = [i.strip() for i in str(value).split(list_delimiter)]
                elif isinstance(value, list) and _checked_type != list:
                    value = list_delimiter.join(value)
            # print('\tvalue AFTER', value)
            return value

    TestParameter._required_params = set() if not required_params else set((i.lower() for i in required_params))
    return TestParameter


class SecurityTestParams(BaseModel):
    _test_params_mapping = {
        'url to scan': 'urls_to_scan',
        'exclusions': 'urls_exclusions',
        'scan location': 'scan_location',
    }

    # the following fields are optional as they are set in test_parameters validator using _test_params_mapping
    urls_to_scan: Optional[List[AnyUrl]]
    urls_exclusions: Optional[List[AnyUrl]]
    scan_location: Optional[str]

    test_parameters: List[test_param_model_factory(['url to scan'])]

    @validator('test_parameters')
    def set_values_from_test_params(cls, value, values):
        for i in value:
            # print('i', i)
            # print('i in', i.name in cls._test_params_mapping.keys())
            if i.name in cls._test_params_mapping.keys():
                values[cls._test_params_mapping[i.name]] = i.default
        return value


class SecurityTestCommon(BaseModel):
    _empty_str_to_none = empty_str_to_none

    project_id: int
    project_name: str
    test_uid: str = str(uuid4())
    name: str
    description: Optional[str]

if __name__ == '__main__':
    import json
    source = json.loads('''
        {"name":"1","description":"","test_parameters":[{"default":"http://sdf","_data":{},"name":"URL to scan","_name_class":"disabled","_name_data":{},"_default_data":{},"type":"URLs","_type_class":"disabled","_type_data":{},"description":"Data","_description_class":"disabled","_description_data":{}},{"_data":{},"name":"11","_name_class":"disabled","_name_data":{},"default":"345","_default_data":{},"type":"","_type_class":"disabled","_type_data":{},"description":"some err","_description_class":"disabled","_description_data":{}},{"_data":{},"name":"Scan location","_name_class":"disabled","_name_data":{},"default":"Carrier default config","_default_data":{},"type":"Item","_type_class":"disabled","_type_data":{},"description":"Data","_description_class":"disabled","_description_data":{}}],"integrations":{},"security_scheduling":[]}
    ''')
    x = SecurityTestParams(test_parameters=source['test_parameters'])
    print(x.test_parameters)
    # print(SecurityTestParams.__dict__)
    print(SecurityTestCommon(**source, project_id=1, project_name='qqq').dict())
