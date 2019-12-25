import sqlite3
import json
from .utils.utils_v2 import *
from .models.election import Election
from .models.result import Result
from .models.result_detail import Result_Detail

load_model()

def get_all( sql='' ):
    conn = sqlite3.connect( DB )
    conn.row_factory = sqlite3.Row # This enables column access by name: row['column_name 
    db = conn.cursor()

    rows = db.execute(sql).fetchall()

    conn.commit()
    conn.close()

    return  [dict(ix) for ix in rows] #CREATE JSON

def insert_result_detail(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executemany('INSERT INTO result_detail (id_result, order_number, vote) '
                 'VALUES (:id_result,:order_number,:vote)', data)
    conn.commit()
    conn.close()

def update_result(data):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.executemany('UPDATE result SET processed = :processed, description = :description WHERE id = :id', data)
    conn.commit()
    conn.close()

def update_election(id_election):
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute('UPDATE election SET status = 2 WHERE id = %s'%id_election)
    conn.commit()
    conn.close()

def check_with_blur(gray_origin, lst_location_cell_origin, path_test='', num_person=10, size_blur = (0,0)):
    temp = validation_full(gray_origin, lst_location_cell_origin, 
                        path_test=path_test, num_person = num_person, size_blur = size_blur)
    total_vote = 0
    for result_detail in temp[1]:
        if 'vote' in result_detail:
            total_vote += result_detail['vote']
    
    return temp, total_vote

def run_all(db):
    results = Result.query.filter_by(processed=0).all()
    # print(results.all()[0].)
    id_election = results[0].id_election
    election = Election.query.filter_by(id=id_election).update({'status': 2})
    election = Election.query.filter_by(id=id_election).first()
    if election.num_persons <= 20:
        num_col = 2
    else:
        num_col=4
        
    # data_result = []
    data_result_detail = []
    gray_origin, lst_location_cell_origin = get_info_table(path_origin='app/static/uploads/images/%s/%s.jpg'%(id_election, id_election), 
    num_person = election.num_persons)

    for result in results:
        temp, total_vote = check_with_blur(gray_origin, lst_location_cell_origin, 
                            path_test=result.image, num_person = election.num_persons)
        if temp[0] == False:
            result.processed = 3
            result.description = temp[1]
        else:
            if total_vote < election.min_persions:
                temp_2, total_vote_2 = check_with_blur(gray_origin, lst_location_cell_origin, 
                            path_test=result.image, num_person = election.num_persons,  size_blur = (3,3))
                if temp_2[0] == False or total_vote_2 < election.min_persions:
                    result.processed = 3
                    result.description = "Số lượng bầu chọn quá ít (%s đại biểu)"%total_vote
                elif total_vote_2 >= election.min_persions and total_vote_2 <= election.max_persions:
                    result.processed = 2
                    data_result_detail.extend(temp_2[1])
                else:
                    result.processed = 3
                    result.description = "Số lượng bầu chọn quá ít (%s đại biểu)"%total_vote_2

            elif total_vote > election.max_persions:
                temp_2, total_vote_2 = check_with_blur(gray_origin, lst_location_cell_origin, 
                            path_test=result.image, num_person = election.num_persons,  size_blur = (3,3))
                if temp_2[0] == False or total_vote_2 > election.max_persions:
                    result.processed = 3
                    result.description = "Số lượng bầu chọn quá nhiều (%s đại biểu)"%total_vote
                elif total_vote_2 >= election.min_persions and total_vote_2 <= election.max_persions:
                    result.processed = 2
                    data_result_detail.extend(temp_2[1])
                else:
                    result.processed = 3
                    result.description = "Số lượng bầu chọn quá nhiều (%s đại biểu)"%total_vote

                # result.processed = 3
                # result.description = "Số lượng bầu chọn quá nhiều (%s đại biểu)"%total_vote
            else:
                result.processed = 2
                data_result_detail.extend(temp[1])

    objects = []
    for dt in data_result_detail:
        rd = Result_Detail(id_result=dt['id_result'], order_number = dt['order_number'], vote= dt['vote'])
        objects.append(rd)
    db.session.bulk_save_objects(objects)
    db.session.commit()
    # insert_result_detail(data_result_detail)
    # update_result(data_result)
    # update_election(election['id)
    return True
