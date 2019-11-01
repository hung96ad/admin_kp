from app import db
class Result(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_election = db.Column(db.Integer, ForeignKey('election.id'))
    image = db.Column(db.String(255))
    # 0 chưa làm gì chờ để detect 
    # 1 đang xử lý 
    # 2 phiếu hợp lệ
    # 3 không hợp lệ
    processed = db.Column(db.Integer)
