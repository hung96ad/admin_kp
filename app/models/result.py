from app import db
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, ForeignKey('election.id'))
    image = db.Column(db.String(255))
    vaild = db.Column(db.Boolean())