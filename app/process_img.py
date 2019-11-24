import sqlite3
import json
from .utils.utils_v2 import *

DB = "sample_db.sqlite"

def get_all( sql='' ):
    conn = sqlite3.connect( DB )
    conn.row_factory = sqlite3.Row # This enables column access by name: row['column_name'] 
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

def run_all(db):
    results = get_all('SELECT * FROM result WHERE processed = 0')
    election = get_all('SELECT * FROM election WHERE id = %s'%results[0]['id'])[0]
    if election['num_persons'] <= 20:
        num_col = 2
    else:
        num_col=4
        
    data_result = []
    data_result_detail = []
    for result in results:
        temp = validation_full(path_origin='app/static/uploads/images/%s/%s.jpg'%(result['id_election'], result['id_election']), 
                            path_test=result['image'], num_col=num_col)
        if temp[0] == False:
            result['processed'] = 3
            result['description'] = temp[1]
        else:
            total_vote = 0
            for result_detail in temp[1]:
                total_vote += result_detail['vote']
                result_detail['id_result'] = result['id']
            if total_vote < election['min_persions'] :
                result['processed'] = 3
                result['description'] = "Số lượng bầu chọn quá ít (%s đại biểu)"%total_vote
            elif total_vote > election['max_persions']:
                result['processed'] = 3
                result['description'] = "Số lượng bầu chọn quá nhiều (%s đại biểu)"%total_vote
            else:
    #             result['results_detail'] = temp[1]
                result['processed'] = 2
                data_result_detail.extend(temp[1])
        data_result.append({
            'id': result['id'],
            'processed': result['processed'],
            'description': result['description']
        })

    insert_result_detail(data_result_detail)
    update_result(data_result)
    update_election(election['id'])

if __name__ == '__main__':
    run_all()