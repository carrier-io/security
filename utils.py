# def json_hook(d: dict):
#     mapper = {
#         'True': True,
#         'False': False
#     }
#     if any([i for i in mapper.keys() if i in d.values()]):
#         for k in d.keys():
#             try:
#                 d[k] = mapper.get(d[k], d[k])
#             except TypeError:
#                 ...
#     return d
