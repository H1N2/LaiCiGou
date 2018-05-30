# coding = utf-8

import app.db.mongo as mongo
from pymongo import MongoClient
import app.logger.logger as logger


# 统计属性中的稀有属性数量
def get_rare_amount(attributes):
    amount = 0
    for attribute in attributes:
        if attribute['rareDegree'] == '稀有':
            amount = amount + 1

    return amount


# 更新旧数据，增加稀有属性数量统计字段
def update_rare_amount():
    count = 0
    for pet in mongo.pet_collection.find():
        count = count + 1
        logger.info('{0}：更新 {1}'.format(count, pet['petId']))
        mongo.pet_collection.update_one({'_id': pet['_id']},
                                        {'$set': {'rareAmount': get_rare_amount(pet['attributes'])}}, upsert=False)


# 检查是否有重复入库的狗狗
def check_duplicate_pet():
    duplicate = []
    index = 0
    for pet in mongo.pet_collection.find():
        index = index + 1
        count = mongo.pet_collection.find({'petId': pet['petId']}).count()
        if count > 1:
            duplicate.append(pet['petId'])
            logger.info('检查第 {0} 条狗狗 {1} ：有重复'.format(index, pet['petId']))
        else:
            logger.info('检查第 {0} 条狗狗 {1} ：无重复'.format(index, pet['petId']))

    logger.info(duplicate)


# 数据库collection拷贝：本地到远程
def db_copy(name):
    src_client = MongoClient()
    src_db = src_client['lai_ci_gou']
    src_coll = src_db[name]

    des_db = mongo.db
    des_coll = des_db[name]

    index = 0
    total = src_coll.find().count()
    # 设置no_cursor_timeout为真，避免处理时间过长报错：pymongo.errors.CursorNotFound: Cursor not found, cursor id: xxxxxxxxx
    cursor = src_coll.find(no_cursor_timeout=True)
    for document in cursor:
        index = index + 1
        des_coll.insert(document)
        if index % 100 == 0:
            logger.info('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))
    logger.info('一共 {0} 份文档，已迁移 {1} 条'.format(total, index))

    cursor.close()


if __name__ == '__main__':
    # check_duplicate_pet()
    # update_rare_amount()
    pass
