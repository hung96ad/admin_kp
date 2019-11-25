from flask_admin import BaseView, expose
import pandas as pd
from flask import request, redirect

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
                JOIN election e ON e.id = a.id_election AND e.is_delete = 0 ORDER BY a.id_election"

        data = self.db.engine.execute(sql)
        return self.render('admin/statistical.html', data=data)
    
    @expose('/detail/<id>/')
    def detail(self, id):
        data = {'id':id}
        sql = "SELECT e.title, a.*, b.num_valid, (a.total-b.num_valid) num_invalid \
            FROM \
        ( SELECT id_election, COUNT( * ) AS total FROM result GROUP BY id_election ) a \
        JOIN ( SELECT id_election, COUNT( * ) AS num_valid FROM result WHERE result.processed = 2 GROUP BY id_election ) AS b ON a.id_election = b.id_election\
        JOIN election e ON e.id = a.id_election AND e.is_delete = 0 AND e.id = %s"%id
        data['content'] = self.db.engine.execute(sql).first()

        sql_2 = "SELECT ed.full_name, a.*\
                FROM election_detail ed \
            	JOIN (SELECT r.id_election, rd.order_number, SUM( rd.vote ) AS total_vote  \
                    FROM result_detail rd \
                    JOIN result r ON r.id = rd.id_result \
                    GROUP BY r.id_election, rd.order_number  ) a ON ed.id_election = a.id_election \
            	AND ed.order_number = a.order_number AND ed.id_election = %s"%(id)
        data['table'] = self.db.engine.execute(sql_2)

        # self.model.query.filter(self.model.id == id).update({"is_delete":True})
        # self.db.session.commit()
        # data = self.model.query.filter(self.model.is_delete == False)
        return self.render('admin/result_detail.html', data=data)
    
    @expose('/error/<id>/')
    def error(self, id):
        sql = "SELECT * FROM result WHERE processed = 3 AND id_election = %s"%id

        data = self.db.engine.execute(sql)
        return self.render('admin/error.html', data=data)
    
    @expose('/export_excel/<id>/')
    def export_excel(self, id):
        data = {}
        sql = "SELECT e.title, a.*, b.num_valid, (a.total-b.num_valid) num_invalid \
            FROM \
        ( SELECT id_election, COUNT( * ) AS total FROM result GROUP BY id_election ) a \
        JOIN ( SELECT id_election, COUNT( * ) AS num_valid FROM result WHERE result.processed = 2 GROUP BY id_election ) AS b ON a.id_election = b.id_election\
        JOIN election e ON e.id = a.id_election AND e.is_delete = 0 AND e.id = %s"%id
        data['content'] = self.db.engine.execute(sql).first()

        sql_2 = "SELECT ed.full_name, a.*\
                FROM election_detail ed \
            	JOIN (SELECT r.id_election, rd.order_number, SUM( rd.vote ) AS total_vote  \
                    FROM result_detail rd \
                    JOIN result r ON r.id = rd.id_result \
                    GROUP BY r.id_election, rd.order_number  ) a ON ed.id_election = a.id_election \
            	AND ed.order_number = a.order_number AND ed.id_election = %s"%(id)
        data['table'] = self.db.engine.execute(sql_2)

        dict_dt = [{'A': "Tên cuộc bầu cử:", "B": data['content']['title'], "C": None}]
        dict_dt.append({'A': "Tổng số phiếu bầu:", "B": data['content']['total'], "C": None})
        dict_dt.append({'A': "Số phiếu bầu hợp lệ:", "B": data['content']['num_valid'], "C": None})
        dict_dt.append({'A': "Số phiếu bầu không hợp lệ:", "B": data['content']['num_invalid'], "C": None})
        dict_dt.append({'A': "Kết quả chi tiết:", "B": "", "C": None})
        dict_dt.append({'A': "STT", "B": "Họ và tên", "C": "Tỷ lệ trúng cử"})
        for dt in data['table']:
            persen = round((dt['total_vote']/data['content']['num_valid'] * 100), 2) 
            str_temp = str(persen) + "%" + " (%s/%s)" %(dt['total_vote'], data['content']['num_valid'])

            dict_dt.append({'A': dt['order_number'], "B": dt['full_name'], "C": str_temp})

        df = pd.DataFrame(dict_dt)
        path_excel = "app/static/uploads/excels/" + "KQBC_%s.xlsx"%id
        df.to_excel(path_excel, index=False, header=False)
        # self.model.query.filter(self.model.id == id).update({"is_delete":True})
        # self.db.session.commit()
        # data = self.model.query.filter(self.model.is_delete == False)
        return redirect(path_excel.replace("app",""))