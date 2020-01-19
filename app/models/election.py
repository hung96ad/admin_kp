from app import db
import datetime

class Election(db.Model):
    __tablename__ = 'election'
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    line_1 = db.Column(db.String(255), nullable=False)
    line_2 = db.Column(db.String(255), nullable=False)
    line_3 = db.Column(db.String(255), nullable=False)
    line_4 = db.Column(db.String(255), nullable=False)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    num_persons = db.Column(db.Integer(), nullable=False)
    min_persions = db.Column(db.Integer(), nullable=False)
    max_persions = db.Column(db.Integer(), nullable=False)
    is_delete = db.Column(db.Boolean(), default=False)
    image = db.Column(db.String(255), default='')
    file = db.Column(db.String(255), default='')
    status = db.Column(db.Integer(), nullable=False)

    def __init__(self, title="", num_persons=0, min_persions=0, max_persions=0, image = "", file="", status=0,
    line_1='', line_2='', line_3='', line_4=''):
        self.title = title
        self.line_1 = line_1
        self.line_2 = line_2
        self.line_3 = line_3
        self.line_4 = line_4
        self.num_persons = num_persons
        self.min_persions = min_persions
        self.max_persions = max_persions
        self.is_delete = False
        self.image = image
        self.file = file
        self.status = status

