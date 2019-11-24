from flask_admin import BaseView, expose
from sqlalchemy import func

class ElectionView(BaseView):
    def __init__(self, name=None, category=None, endpoint=None, url=None,
                 static_folder=None, static_url_path=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None,
                 model=None, db=None):
        """
            Constructor.

            :param name:
                Name of this view. If not provided, will default to the class name.
            :param category:
                View category. If not provided, this view will be shown as a top-level menu item. Otherwise, it will
                be in a submenu.
            :param endpoint:
                Base endpoint name for the view. For example, if there's a view method called "index" and
                endpoint is set to "myadmin", you can use `url_for('myadmin.index')` to get the URL to the
                view method. Defaults to the class name in lower case.
            :param url:
                Base URL. If provided, affects how URLs are generated. For example, if the url parameter
                is "test", the resulting URL will look like "/admin/test/". If not provided, will
                use endpoint as a base url. However, if URL starts with '/', absolute path is assumed
                and '/admin/' prefix won't be applied.
            :param static_url_path:
                Static URL Path. If provided, this specifies the path to the static url directory.
            :param menu_class_name:
                Optional class name for the menu item.
            :param menu_icon_type:
                Optional icon. Possible icon types:

                 - `flask_admin.consts.ICON_TYPE_GLYPH` - Bootstrap glyph icon
                 - `flask_admin.consts.ICON_TYPE_FONT_AWESOME` - Font Awesome icon
                 - `flask_admin.consts.ICON_TYPE_IMAGE` - Image relative to Flask static directory
                 - `flask_admin.consts.ICON_TYPE_IMAGE_URL` - Image with full URL
            :param menu_icon_value:
                Icon glyph name or URL, depending on `menu_icon_type` setting
        """
        self.name = name
        self.category = category
        self.endpoint = self._get_endpoint(endpoint)
        self.url = url
        self.static_folder = static_folder
        self.static_url_path = static_url_path
        self.menu = None

        self.menu_class_name = menu_class_name
        self.menu_icon_type = menu_icon_type
        self.menu_icon_value = menu_icon_value

        # Initialized from create_blueprint
        self.admin = None
        self.blueprint = None
        self.model = model
        self.db = db

        # Default view
        if self._default_view is None:
            raise Exception(u'Attempted to instantiate admin view %s without default view' % self.__class__.__name__)


    @expose('/')
    def index(self):
        data = self.model.query.filter(self.model.is_delete == False)
        return self.render('admin/election.html', data=data)
    
    @expose('/delete/<id>/', methods=('GET', 'POST'))
    def delete(self, id):
        self.model.query.filter(self.model.id == id).update({"is_delete":True})
        self.db.session.commit()
        data = self.model.query.filter(self.model.is_delete == False)
        return self.render('admin/election.html', data=data)
        
    @expose('/edit/<id>/', methods=('GET', 'POST'))
    def edit(self, id):
        self.name = "Sửa thông tin cuộc bầu cử"
        data = self.model.query.get(id)
        return self.render('admin/edit.html', data=data)

    @expose('/upload_zip/<id>/', methods=('GET', 'POST'))
    def upload(self, id=0):
        data = {"type": 0}
        if id == "0":
            data['data'] = self.model.query.filter(self.model.is_delete == False, self.model.status != 3)      
        else:
            data = {"type": 1}
            data['data'] = self.model.query.get(id)

        self.name = "Nộp phiếu bầu cử"
        return self.render('admin/upload_zip.html', data=data)
    