import sqlite3
import json
from .utils.utils_v2 import *
from .models.election import Election
from .models.result import Result
from .models.result_detail import Result_Detail
from .models.eletion_detail import Eletion_Detail

def run_all(db):
    results = Result.query.filter_by(processed=0).all()
    id_election = results[0].id_election
    election = Election.query.filter_by(id=id_election).update({'status': 2})
    election = Election.query.filter_by(id=id_election).first()
    eds = Eletion_Detail.query.filter_by(id_election=id_election).filter_by(is_delete=0).all()
    if election.num_persons <= 20:
        num_col = 2
    else:
        num_col=4
    list_people = {}
    for ed in eds:
        list_people[ed.order_number] = ed.full_name
    data_result_detail = []

    for result in results:
        temp = validation_full(list_people, path_test=result.image, num_person = election.num_persons)
        if temp[0] == False:
            result.processed = 3
            result.description = temp[1]
        else:
            total_vote = 0
            for result_detail in temp[1]:
                total_vote += result_detail['vote']
                result_detail['id_result'] = result.id
            if total_vote < election.min_persions:
                result.processed = 3
                result.description = "Số lượng bầu chọn quá ít (%s đại biểu)"%total_vote
            elif total_vote > election.max_persions:
                result.processed = 3
                result.description = "Số lượng bầu chọn quá nhiều (%s đại biểu)"%total_vote
            else:
                result.processed = 2
                data_result_detail.extend(temp[1])

    objects = []
    for dt in data_result_detail:
        rd = Result_Detail(id_result=dt['id_result'], order_number = dt['order_number'], vote= dt['vote'])
        objects.append(rd)
    db.session.bulk_save_objects(objects)
    db.session.commit()
    return True