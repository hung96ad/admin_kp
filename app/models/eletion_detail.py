from app import db
class Eletion_Detail(db.Model):
    __tablename__ = 'election_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, db.ForeignKey('election.id'))
    full_name = db.Column(db.String(255))
    order_number = db.Column(db.Integer)

    def __init__(self, full_name="", id_election=0, order_number=0):
        self.full_name = full_name
        self.id_election = id_election
        self.order_number = order_number

