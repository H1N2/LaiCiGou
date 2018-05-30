# coding = utf-8

from pymongo import MongoClient
from app.config.cfg import MONGODB_HOST as mongo_host
from app.config.cfg import MONGODB_PORT as mongo_port
from app.config.cfg import MONGODB_USERNAME as user_name
from app.config.cfg import MONGODB_PASSWORD as password

mongo_client = MongoClient(mongo_host, mongo_port)
mongo_client.lai_ci_gou.authenticate(user_name, password)

db = mongo_client['lai_ci_gou']

pet_collection = db['pets']
attribute_collection = db['attributes']
breed_prob_collection = db['breedProbability']
order_collection = db['orders']
calculus_collection = db['calculus']