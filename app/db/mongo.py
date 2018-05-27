# coding = utf-8

from pymongo import MongoClient
from cfg import MONGODB_HOST as mongo_host
from cfg import MONGODB_PORT as mongo_port
from cfg import MONGODB_USERNAME as user_name
from cfg import MONGODB_PASSWORD as password

mongo_client = MongoClient(mongo_host, mongo_port)
mongo_client.lai_ci_gou.authenticate(user_name, password)

db = mongo_client.lai_ci_gou
