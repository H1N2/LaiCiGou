# coding = utf-8
from datetime import datetime
from datetime import timedelta
import pymongo
import json
import app.db.mongo as mongo
import app.logger.logger as logger
from app.config.cfg import COOKIE as cookie
from flask import render_template
from flask import Flask, request
from app.order import Order
from counter import Counter
from lai_ci_gou import LaiCiGou

app = Flask(__name__)


class LaiCiGouWebManager(LaiCiGou):
    def __init__(self, cookie):
        super(LaiCiGouWebManager, self).__init__(cookie)

    def show_user_profile(username):
        return 'User %s' % username

    def render_html_template(self, name):
        return render_template(name)

    def get_pets_attributes_summary_data(self):
        rare_degrees = ['普通', '稀有', '卓越', '史诗', '神话', '传说']
        rare_amounts = {0: '无', 1: '1 稀', 2: '2 稀', 3: '3 稀', 4: '4 稀', 5: '5 稀', 6: '6 稀', 7: '7 稀', 8: '8 稀'}
        attributes_names = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']

        results = {'results': []}

        # 按稀有度统计狗狗数据
        pets_data = {'text': '狗狗（稀有度）', 'data': []}
        for rare_degree in rare_degrees:
            count = mongo.pet_collection.find({'rareDegree': rare_degree}).count()
            pets_data['data'].append({'name': rare_degree, 'value': count})

        results['results'].append(pets_data)

        # 按稀有属性数量统计勾过数据
        rare_amount_data = {'text': '狗狗（稀有数）', 'data': []}
        for rare_amount in rare_amounts:
            count = mongo.pet_collection.find({'rareAmount': rare_amount}).count()
            rare_amount_data['data'].append({'name': rare_amounts[rare_amount], 'value': count})

        results['results'].append(rare_amount_data)

        # 统计所有属性数据
        for attribute_name in attributes_names:
            attributes_data = {'text': attribute_name, 'data': []}
            for attribute_data in mongo.attribute_collection.find({'name': attribute_name}):
                name = attribute_data['value'] if not attribute_data['rareDegree'] else '{0}({1})'.format(
                    attribute_data['value'],
                    attribute_data['rareDegree'])

                attributes_data['data'].append({'name': name, 'value': attribute_data['amount']})
            results['results'].append(attributes_data)

        return json.dumps(results)

    def _get_oldest_order_trans_date(self):
        for order in mongo.order_collection.find({'txnStatus': 2}).sort([("transDate", pymongo.ASCENDING)]):
            return order['transDate']

    def _days_between_dates(self, date1, date2):
        date_time1 = datetime.strptime(date1, '%Y-%m-%d')
        date_time2 = datetime.strptime(date2, '%Y-%m-%d')
        return (date_time1 - date_time2).days

    def get_asset_data(self):
        status = {1: "已卖出", 2: "已买入", 3: "繁育收入", 4: "繁育支出"}
        txnStatus = {0: "上链中", 1: "上链中", 2: "成功", 3: "失败", 4: "失败"}

        now = datetime.now().strftime("%Y-%m-%d")
        oldest_date = self._get_oldest_order_trans_date()
        days = self._days_between_dates(now, oldest_date)

        dates, incomes, expends, totals = [], [], [], []
        from_date = datetime.now() + timedelta(days=-days)
        for day in range(days + 1):
            date = (from_date + timedelta(days=day)).strftime('%Y-%m-%d')
            income, expend, amount = 0, 0, 0
            for order in mongo.order_collection.find({'transDate': date, 'txnStatus': 2}):
                amount = float(order['amount'])
                if order['type'] == 1 or order['type'] == 3:
                    income = round(income + amount, 2)
                if order['type'] == 2 or order['type'] == 4:
                    expend = round(expend + amount, 2)

            dates.append(date)
            incomes.append(income)
            expends.append(expend)

        # 根据最新的微积分总数和每天交易记录反推过去每天的微积分总数（有误差，因为交易记录不包含每天签到和初始赠送记录）
        # total = float(self.calculus_coll.find_one()['amount'])
        order = Order(cookie, clear=False)
        total = order.get_save_latest_calculus()
        totals.append(round(total))
        for i in range(len(dates) - 1):
            j = len(dates) - 1 - i
            margin = incomes[j] - expends[j]
            total = total - margin
            totals.append(round(total))
        return json.dumps(
            {'dates': dates, 'incomes': incomes, 'expends': expends, 'totals': totals[::-1]})  # totals[::-1] 列表反转

    def get_breed_probability_data(self):
        data = mongo.breed_prob_collection.find_one()
        results = {}
        for rare in range(9):
            rare = str(rare)
            father_mother, amount = [], []
            total = 0
            for f in range(9):
                for m in range(9):
                    fm = str(f) + '-' + str(m)
                    amount_value = 0
                    for d in data[rare]:
                        if fm in d:
                            amount_value = d[fm]

                    total = total + amount_value
                    father_mother.append(fm)
                    amount.append(amount_value)

            results[rare] = {'fatherMother': father_mother, 'childrenAmount': amount, 'childrenTotal': total}
        return json.dumps(results)

    def get_baby_attributes(self):
        counter = Counter(self.cookie)
        pet_id = request.form['petId']
        result = counter.get_baby_attribute_details_api(pet_id)
        return json.dumps(result)


server = LaiCiGouWebManager(cookie)


@app.route('/')
def home_page():
    return server.render_html_template('home.html')


@app.route('/user/<username>')
def show_user_profile():
    return server.show_user_profile()


@app.route('/pie/')
def pie_page():
    return server.render_html_template('pie.html')


@app.route("/pie/getData", methods=['POST'])
def get_pets_attributes_summary_data():
    return server.get_pets_attributes_summary_data()


@app.route('/asset/')
def asset_page():
    return server.render_html_template('asset.html')


@app.route("/asset/getAssetData", methods=['POST'])
def get_asset_data():
    return server.get_asset_data()


@app.route('/breed/')
def breed_page():
    return server.render_html_template('breedProb.html')


@app.route("/breed/getBreedProbabilityData", methods=['POST'])
def get_breed_probability_data():
    return server.get_breed_probability_data()


@app.route('/recognise/')
def recognise_page():
    return server.render_html_template('recogniseBaby.html')


@app.route("/recognise/getBabyAttributes", methods=['POST'])
def get_baby_attributes():
    return server.get_baby_attributes()


if __name__ == '__main__':
    pass
