from .mymodelview import MyModelView
class ElectionView(MyModelView):
    column_editable_list = ['line_1','line_2','line_3','line_4', 'time_created', 'num_persons','min_persions']
    column_searchable_list = column_editable_list
    column_exclude_list = ['is_delete']
    # form_excluded_columns = column_exclude_list
    column_details_exclude_list = column_exclude_list
    column_filters = column_editable_list