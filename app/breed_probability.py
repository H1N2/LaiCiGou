# coding = utf-8

import copy
from logger import log
from app.db.mongo import db


# 统计狗狗及双亲稀有属性数量之间的关系
def count_breed_data():
    pets = db['pets']
    breed_prob = db['breed_probability']
    results = {}
    index = 0
    total1 = pets.find().count()
    total = pets.find({'fatherId': {'$ne': None}}).count()

    # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
    cursor = pets.find({'fatherId': {'$ne': None}}, no_cursor_timeout=True)
    for pet in cursor:
        index = index + 1
        father = pets.find_one({'petId': pet['fatherId']})
        mother = pets.find_one({'petId': pet['motherId']})
        if not father or not mother:
            continue

        key = '{0}-{1}'.format(father['rareAmount'], mother['rareAmount'])

        rare_amount = str(pet['rareAmount'])
        if rare_amount in results:
            has_key = False
            for p in results[rare_amount]:
                if key in p:
                    p[key] = p[key] + 1
                    has_key = True
                    break

            if not has_key:
                results[rare_amount].append({key: 1})
        else:
            results[rare_amount] = [{key: 1}]

        if index % 100 == 0:
            log('一共 {0} 条狗狗，已统计处理 {1} 条'.format(total, index))

        if index % 10000 == 0:
            new_results = copy.deepcopy(results)
            new_results['no'] = index / 10000
            breed_prob.insert(new_results)
    cursor.close()

    new_results = copy.deepcopy(results)
    new_results['no'] = index / 10000
    breed_prob.insert(new_results)


if __name__ == '__main__':
    count_breed_data()
