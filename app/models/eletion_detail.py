from app import db
class Eletion_Detail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, ForeignKey('election.id'))
    first_name = db.Column(db.String(255))
    last_name = db.Column(db.String(255))
    order_number = db.Column(db.Integer)

