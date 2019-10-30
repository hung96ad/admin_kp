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

from .views.mymodelview import MyModelView
from .views.userview import UserView
from .views.electionview import ElectionView
from .views.customview import CustomView
from .views.add import AddView
from .views.update import UpdateView
import warnings

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
        if request.files:
            if "input_file" in request.files.keys():
                file_data = request.files["input_file"]
                file_data.save(file_data.filename)  
                return redirect(request.url)

    return render_template('index.html')
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