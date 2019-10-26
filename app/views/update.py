from flask_admin import BaseView, expose

class UpdateView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/update.html')