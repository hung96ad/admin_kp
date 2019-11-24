from app import db
class Eletion_Detail(db.Model):
    __tablename__ = 'election_detail'
    
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, db.ForeignKey('election.id'))
    full_name = db.Column(db.String(255))
    order_number = db.Column(db.Integer)
    is_delete = db.Column(db.Boolean(), default=False)

    def __init__(self, full_name="", id_election=0, order_number=0, is_delete=False):
        self.full_name = full_name
        self.id_election = id_election
        self.order_number = order_number
        self.is_delete = is_delete

