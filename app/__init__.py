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
from .views.customview import CustomView
from .views.add import AddView
from .views.update import UpdateView

from .controllers.gen_template import gen_by_ho_ten

import warnings
import pandas as pd

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
        election_id = db.session.query(db.func.max(Election.id)).scalar() + 1
        line_1 = request.form.get('line_1')
        line_2 = request.form.get('line_2')
        line_3 = request.form.get('line_3')
        line_4 = request.form.get('line_4')
        line = [line_1, line_2, line_3, line_4]
        title = ' '.join(filter(None, line))
        min_persions = request.form.get('number')
        file_data = request.files["input_file"]
        file_data.filename = str(election_id) + ".xlsx"
        path_excel = app.config['EXCEL'] + file_data.filename
        file_data.save(path_excel)

        # sinh ra file ảnh
        ho_ten = pd.read_excel(path_excel)
        num_persons = ho_ten.shape[0]
        ho_ten = ho_ten.sort_values(['Tên', 'Họ']).reset_index(drop=True)
        ho_ten['full_name'] = ho_ten['Họ'] + " " + ho_ten['Tên']
        image = gen_by_ho_ten(ho_ten['full_name'], election_id, line, app.config['IMAGE'])

        # add vao db
        objects = []
        elec = Election(title = title, num_persons=ho_ten.shape[0], min_persions=min_persions, image=image, file=path_excel)
        objects.append(elec)
        
        for i in range(ho_ten.shape[0]):
            ed = Eletion_Detail(full_name=ho_ten['full_name'][i], id_election=election_id, order_number=i+1)
            objects.append(ed)
        
        db.session.bulk_save_objects(objects)
        db.session.commit()

    return render_template('upload_file.html', user_image = image)
# Create admin
admin = flask_admin.Admin(
    app,
    'My Dashboard',
    base_template='my_master.html',
    template_mode='bootstrap3',
)

# Add model views
admin.add_view(AddView(name="Thêm cuộc bầu cử", endpoint='add', menu_icon_type='fa', menu_icon_value='fa-calendar-plus-o',))
admin.add_view(UpdateView(name="Thêm ảnh cuộc bầu cử", endpoint='update', menu_icon_type='fa', menu_icon_value='fa-edit (alias)',))

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