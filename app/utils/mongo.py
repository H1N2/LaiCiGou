# coding = utf-8

from pymongo import MongoClient
from logger import log
from app.db.mongo import db


# 统计属性中的稀有属性数量
def get_rare_amount(attributes):
    amount = 0
    for attribute in attributes:
        if attribute['rareDegree'] == '稀有':
            amount = amount + 1

    return amount


# 更新旧数据，增加稀有属性数量统计字段
def update_rare_amount():
    client = MongoClient()
    db = client['lai_ci_gou']
    pets = db['pets']
    count = 0
    for pet in pets.find():
        count = count + 1
        log('{0}：更新 {1}'.format(count, pet['petId']))
        pets.update_one({'_id': pet['_id']}, {'$set': {'rareAmount': get_rare_amount(pet['attributes'])}}, upsert=False)


# 检查是否有重复入库的狗狗
def check_duplicate_pet():
    client = MongoClient()
    db = client['lai_ci_gou']
    pets = db['pets']
    duplicate = []
    index = 0
    for pet in pets.find():
        index = index + 1
        count = pets.find({'petId': pet['petId']}).count()
        if count > 1:
            duplicate.append(pet['petId'])
            log('检查第 {0} 条狗狗 {1} ：有重复'.format(index, pet['petId']))
        else:
            log('检查第 {0} 条狗狗 {1} ：无重复'.format(index, pet['petId']))

    log(duplicate)


# 统计狗狗及双亲稀有属性数量之间的关系
def db_copy(name):
    src_client = MongoClient()
    src_db = src_client['lai_ci_gou']
    src_coll = src_db[name]

    des_db = db
    des_coll = des_db[name]

    index = 0
    total = src_coll.find().count()
    # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
    cursor = src_coll.find(no_cursor_timeout=True)
    for document in cursor:
        index = index + 1
        des_coll.insert(document)
        if index % 100 == 0:
            log('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))
    log('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))

    cursor.close()


if __name__ == '__main__':
    # check_duplicate_pet()
    # update_rare_amount()
    db_copy('pets')
