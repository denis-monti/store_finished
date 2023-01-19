from flask import current_app



def add_to_index(index, model):
    if not current_app.elasticsearch:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    current_app.elasticsearch.index(index=index, doc_type=index, id=model.id_Product,
                                    body=payload)

def remove_from_index(index, model):
    if not current_app.elasticsearch:
        return
    current_app.elasticsearch.delete(index=index, doc_type=index, id=model.id_Product)

# def query_index(index, query, page, per_page):
#     if not current_app.elasticsearch:
#         return [], 0, []
#     search = current_app.elasticsearch.search(
#         index=index, doc_type=index,
#         body={'query': {'multi_match': {"query": query, 'operator': 'and', 'fuzziness': 'auto', 'fields': ['*']}},
#
#
#               'from': (page - 1) * per_page, 'size': per_page})
#     ids = [int(hit['_id']) for hit in search['hits']['hits']]
#
#     search_sum_page = current_app.elasticsearch.search(
#         index=index, doc_type=index,
#         body={'query': {'multi_match': {'query': query, 'fields': ['*']}},
#               'from': (page - 1), 'size': 900})
#     ids_sum = [int(hit['_id']) for hit in search_sum_page['hits']['hits']]
#     # return  ids_sum
#     return ids, search['hits']['total'], ids_sum
def query_index(index, query, page):
    if not current_app.elasticsearch:
        return []
    search = current_app.elasticsearch.search(
        index=index, doc_type=index,
        body={'query': {'multi_match': {"query": query, 'operator': 'and', 'fuzziness': 'auto', 'fields': ['*']}},


              'from': (page - page), 'size': 1000})
    ids_sum = [int(hit['_id']) for hit in search['hits']['hits']]
    return search['hits']['total'], ids_sum