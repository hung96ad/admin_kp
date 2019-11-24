from flask_admin import BaseView, expose

class ResultView(BaseView):
    def __init__(self, name=None, category=None, endpoint=None, url=None,
                 static_folder=None, static_url_path=None,
                 menu_class_name=None, menu_icon_type=None, menu_icon_value=None, db=None):
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
        self.db = db

        # Default view
        if self._default_view is None:
            raise Exception(u'Attempted to instantiate admin view %s without default view' % self.__class__.__name__)


    @expose('/')
    def index(self):
        sql = "SELECT e.title, a.*, b.num_valid, (a.total-b.num_valid) num_invalid \
                    FROM \
                ( SELECT id_election, COUNT( * ) AS total FROM result GROUP BY id_election ) a \
                JOIN ( SELECT id_election, COUNT( * ) AS num_valid FROM result WHERE result.processed = 2 GROUP BY id_election ) AS b ON a.id_election = b.id_election\
                JOIN election e ON e.id = a.id_election AND e.is_delete = 0"

        data = self.db.engine.execute(sql)
        return self.render('admin/statistical.html', data=data)
    
    @expose('/detail/<id>/')
    def detail(self, id):
        # self.model.query.filter(self.model.id == id).update({"is_delete":True})
        # self.db.session.commit()
        # data = self.model.query.filter(self.model.is_delete == False)
        return self.render('admin/result_detail.html')
    
    # @expose('/upload_zip/<id>/', methods=('GET', 'POST'))
    # def upload(self, id):
    #     return self.render('admin/upload_zip.html', data={'id': id})
    