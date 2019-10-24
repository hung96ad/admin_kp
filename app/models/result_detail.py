from app import db
class Result_Detail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_result = db.Column(db.Integer, ForeignKey('result.id'))
    order_number = db.Column(db.Integer)
    vote = db.Column(db.Boolean())