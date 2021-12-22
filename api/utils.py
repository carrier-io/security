class ValidationError(Exception):
    def __init__(self, data):
        super().__init__()
        self.data = data


def format_test_parameters(test_parameters: list) -> dict:
    REQUIRED_PARAMETERS = set(i.lower() for i in ['URL to scan'])
    result = dict()
    errors = dict()
    item_value_key = 'default'
    for index, i in enumerate(test_parameters):
        name = i.get('name').lower()

        for k in set(i.keys()):
            if k.startswith('_'):
                del i[k]

        data_type = i.get('type', '').lower()
        if data_type == 'list':
            if not isinstance(i[item_value_key], list):
                i[item_value_key] = [x.strip() for x in i[item_value_key].split(',')]
        elif data_type in ('integer', 'number'):
            try:
                if isinstance(i[item_value_key], list):
                    i[item_value_key] = float(i[item_value_key][0])
                else:
                    i[item_value_key] = float(i[item_value_key])
            except ValueError as e:
                errors[index] = str(e)
        elif data_type in ('string', ''):
            if isinstance(i[item_value_key], list):
                i[item_value_key] = ','.join(i[item_value_key])
            i[item_value_key] = i[item_value_key].strip()

        if name in REQUIRED_PARAMETERS and not i[item_value_key]:
            errors[index] = f'{name} is required'

        result[name] = i
    if errors:
        raise ValidationError(errors)
    return result
