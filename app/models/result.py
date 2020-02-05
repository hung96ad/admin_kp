from app import db
class Result(db.Model):
    __tablename__ = 'result'
    
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, db.ForeignKey('election.id'))
    stt = db.Column(db.Integer)
    image = db.Column(db.String(255))
    description = db.Column(db.String(255))
    # 0 chưa làm gì chờ để detect 
    # 1 đang xử lý 
    # 2 phiếu hợp lệ
    # 3 không hợp lệ
    processed = db.Column(db.Integer)

    def __init__(self, id_election=1, stt=0, image='', processed=0, description=''):
        self.id_election = id_election
        self.stt = stt
        self.image = image
        self.processed = processed        
        self.description = description        
