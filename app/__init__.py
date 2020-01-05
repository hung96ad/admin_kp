#!venv/bin/python
import os
from flask import Flask, url_for, redirect, render_template, request, abort
from flask_sqlalchemy import SQLAlchemy
from flask_security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required, current_user
from flask_security.utils import encrypt_password
import flask_admin
from flask_admin.contrib import sqla
from flask_admin import helpers as admin_helpers
from flask_admin import BaseView, expose
from sqlalchemy.sql.expression import func

from .views.mymodelview import MyModelView
from .views.userview import UserView
from .views.electionview import ElectionView
from .views.resultview import ResultView
from .views.customview import CustomView
from .views.add import AddView
from .views.update import UpdateView

from .controllers.gen_template import gen_by_ho_ten

import warnings
import pandas as pd
import zipfile
import patoolib
import uuid
import time
from subprocess import Popen, PIPE, STDOUT

def fxn():
    warnings.warn("deprecated", DeprecationWarning)

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    fxn()


# Create Flask application
app = Flask(__name__)
app.config.from_pyfile('../config.py')
db = SQLAlchemy(app)

from .models.role import Role
from .models.user import User
from .models.election import Election
from .models.eletion_detail import Eletion_Detail
from .models.result import Result
from .models.result_detail import Result_Detail
from .process_img import run_all
# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Flask views
@app.route('/')
def index():
    return render_template('index.html')

@app.route("/upload-file", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        election_id = request.form.get('id')
        line_1 = request.form.get('line_1')
        line_2 = request.form.get('line_2')
        line_3 = request.form.get('line_3')
        line_4 = request.form.get('line_4')
        line = [line_1, line_2, line_3, line_4]
        title = ' '.join(filter(None, line))
        min_persions = request.form.get('min_persions')
        max_persions = request.form.get('max_persions')

        if election_id is None:
            election_id = db.session.query(db.func.max(Election.id)).scalar()
            if election_id is None:
                election_id = 1
            else:
                election_id += 1
            file_data = request.files["input_file"]
            file_data.filename = str(election_id) + ".xlsx"
            path_excel = app.config['EXCEL'] + file_data.filename
            file_data.save(path_excel)

            # sinh ra file ảnh
            ho_ten = pd.read_excel(path_excel)
            num_persons = ho_ten.shape[0]
            ho_ten['full_name'] = ho_ten['Họ'] + " " + ho_ten['Tên']
            image = gen_by_ho_ten(ho_ten['full_name'].str.upper(), election_id, line, app.config['IMAGE'])

            # add vao db
            objects = []
            elec = Election(title = title, num_persons=ho_ten.shape[0], min_persions=min_persions, max_persions=max_persions, image=image, file=path_excel,
            line_1=line_1, line_2=line_2, line_3=line_3, line_4=line_4)
            objects.append(elec)
            
            for i in range(ho_ten.shape[0]):
                ed = Eletion_Detail(full_name=ho_ten['full_name'][i], id_election=election_id, order_number=i+1)
                objects.append(ed)
            
            db.session.bulk_save_objects(objects)
            db.session.commit()
        else:
            elec = Election.query.get(election_id)
            file_data = request.files["input_file"]
            if file_data is None:
                path_excel = request.form.get('file')
                ho_ten = pd.read_excel(path_excel)
                ho_ten['full_name'] = ho_ten['Họ'] + " " + ho_ten['Tên']
            else:
                file_data.filename = str(election_id) + ".xlsx"
                path_excel = app.config['EXCEL'] + file_data.filename
                ho_ten = pd.read_excel(path_excel)
                ho_ten['full_name'] = ho_ten['Họ'] + " " + ho_ten['Tên']

                file_data.save(path_excel)
                ede = Eletion_Detail.query.filter(Eletion_Detail.id_election == election_id).update({"is_delete":True})

                objects = []
                for i in range(ho_ten.shape[0]):
                    ed = Eletion_Detail(full_name=ho_ten['full_name'][i], id_election=election_id, order_number=i+1)
                    objects.append(ed)
                
                db.session.bulk_save_objects(objects)

            image = gen_by_ho_ten(ho_ten['full_name'].str.upper(), election_id, line, app.config['IMAGE'])

            elec.title = title
            elec.line_1 = line_1
            elec.line_2 = line_2
            elec.line_3 = line_3
            elec.line_4 = line_4
            elec.min_persions = min_persions
            elec.max_persions = max_persions
            db.session.commit()

    return render_template('upload_file.html', user_image = image)

@app.route("/upload_zip/", methods=["GET", "POST"])
def upload_zip():
    start_time = time.time()
    if request.method == "POST":
        id = request.form.get('comp_select')
        file_data = request.files["input_file"]
        path_folder = app.config['IMAGE'] + str(id) +  '/' + str(uuid.uuid4())
        path_file = path_folder + file_data.filename
        file_data.save(path_file)
        if path_file.split('.')[-1] == 'zip':
            with zipfile.ZipFile(path_file, 'r') as zip_ref:
                zip_ref.extractall(path_folder)
        else:
            os.makedirs(path_folder, exist_ok=True)
            patoolib.extract_archive(path_file, outdir=path_folder)
        list_image = os.listdir(path_folder)
        if not os.path.isfile(path_folder + '/' + list_image[0]):
            path_folder += '/' + list_image[0]
            list_image = os.listdir(path_folder)

        objects = []
        for image in list_image:
            if image.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
                rs = Result(id_election=id, image = path_folder + '/' + image)
                objects.append(rs)
        
        el = Election.query.filter_by(id=id).update({'status': 1})
        db.session.bulk_save_objects(objects)
        # db.session.commit()
        process_img = run_all(db)
        if process_img == True:
            return render_template('upload_zip_success.html', data={'id': id, 
            'message': 'Xử lý thành công trong thời gian %ss. Trang sẽ tự động trở về kết quả bầu cử sau 2s.'%(time.time()-start_time)})
        else:
            db.session.rollback()
    return render_template('upload_zip_success.html', data={"Gặp lỗi trong quá trình xử lý"})

# Create admin
admin = flask_admin.Admin(
    app,
    'Phần mềm kiểm phiếu',
    base_template='my_master.html',
    template_mode='bootstrap3'
)
# print(Election().all())
# Add model views
admin.add_view(AddView(name="Thêm mới bầu cử", endpoint='add', menu_icon_type='fa', menu_icon_value='fa-calendar-plus-o',))
admin.add_view(ElectionView(endpoint='election', menu_icon_type='fa', menu_icon_value='fa-server', name="Quản lý danh sách các cuộc bầu cử", model=Election, db=db))
admin.add_view(ResultView(endpoint='statistical', menu_icon_type='fa', menu_icon_value='fa-table', name="Thống kê bầu cử", db=db))
# admin.add_view(UpdateView(name="Bổ sung phiếu bầu cử", endpoint='update', menu_icon_type='fa', menu_icon_value='fa-edit (alias)',))
# define a context processor for merging flask-admin's template context into the
# flask-security views.
@security.context_processor
def security_context_processor():
    return dict(
        admin_base_template=admin.base_template,
        admin_view=admin.index_view,
        h=admin_helpers,
        get_url=url_for
    )

if __name__ == '__main__':

    # # Build a sample db on the fly, if one does not exist yet.
    # app_dir = os.path.realpath(os.path.dirname(__file__))
    # database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])

    # Start app
    app.run(debug=True)