from app import db
import datetime

class Election(db.Model):
    __tablename__ = 'election'
    id = db.Column(db.Integer(), primary_key=True)
    line_1 = db.Column(db.String(255), nullable=False)
    line_2 = db.Column(db.String(255), default='')
    line_3 = db.Column(db.String(255), default='')
    line_4 = db.Column(db.String(255), default='')
    time_created = db.Column(db.DateTime(), default=datetime.datetime.now())
    num_persons = db.Column(db.Integer(), nullable=False)
    min_persions = db.Column(db.Integer(), nullable=False)
    is_delete = db.Column(db.Boolean(), default=False)

