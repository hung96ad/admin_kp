from app import db
import datetime

class Election(db.Model):
    __tablename__ = 'election'
    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    time_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    num_persons = db.Column(db.Integer(), nullable=False)
    min_persions = db.Column(db.Integer(), nullable=False)
    is_delete = db.Column(db.Boolean(), default=False)
    image = db.Column(db.String(255), default='')
    file = db.Column(db.String(255), default='')

    def __init__(self, title="", num_persons=0, min_persions=0, image = "", file=""):
        self.title = title
        self.num_persons = num_persons
        self.min_persions = min_persions
        self.is_delete = False
        self.image = image
        self.file = file

