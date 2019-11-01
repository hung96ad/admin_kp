from .mymodelview import MyModelView
class ElectionView(MyModelView):
    column_editable_list = ['min_persions']
    column_searchable_list = ['title', 'time_created', 'num_persons','min_persions', 'image', 'file']
    column_exclude_list = ['is_delete']
    # form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_searchable_list