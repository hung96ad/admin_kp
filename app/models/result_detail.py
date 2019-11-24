from app import db
class Result_Detail(db.Model):
    __tablename__ = 'result_detail'
    id = db.Column(db.Integer, primary_key=True)
    id_result = db.Column(db.Integer, db.ForeignKey('result.id'))
    order_number = db.Column(db.Integer)
    vote = db.Column(db.Boolean())

    def __init__(self, id_result=1, order_number=0, vote=True):
        self.id_result = id_result
        self.order_number = order_number
        self.vote = vote        