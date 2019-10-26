from flask_admin import BaseView, expose

class AddView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/add.html')