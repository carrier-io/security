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

    test_parameters: List[test_param_model_factory(['url to scan'], type_mapping_by_name={'url to scan': List[AnyUrl]})]

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
    test_uid: Optional[str]
    name: str
    description: Optional[str] = ''

    @root_validator
    def set_uuid(cls, values):
        # print('RV', values)
        if not values.get('test_uid'):
            values['test_uid'] = str(uuid4())
        return values


if __name__ == '__main__':
    import json
    source = json.loads('''
        {"name":"df","description":"","test_parameters":[{"_data":{},"name":"URL to scan","_name_class":"disabled","_name_data":{},"default":"","_default_data":{},"type":"URLs","_type_class":"disabled","_type_data":{},"description":"Data","_description_class":"disabled","_description_data":{}},{"_data":{},"name":"Exclusions","_name_class":"disabled","_name_data":{},"default":"","_default_data":{},"type":"List","_type_class":"disabled","_type_data":{},"description":"Data","_description_class":"disabled","_description_data":{}},{"_data":{},"name":"Scan location","_name_class":"disabled","_name_data":{},"default":"Carrier default config","_default_data":{},"type":"Item","_type_class":"disabled","_type_data":{},"description":"Data","_description_class":"disabled","_description_data":{}}],"integrations":{},"security_scheduling":[]}
    ''')
    tp = json.loads('''
    {"default":"","description":"Data","name":"Exclusions","type":"List","_description_class":"disabled","_name_class":"disabled","_type_class":"disabled"}
    ''')
    # x = SecurityTestParams(test_parameters=source['test_parameters'])
    # print(x.test_parameters)
    # print(SecurityTestParams.__dict__)
    print(SecurityTestCommon(**source, project_id=1, project_name='qqq').dict())

    # pd_tp = test_param_model_factory(['exclusions1'])
    # pd_obj = pd_tp(**tp)
    # print(pd_obj.dict())
