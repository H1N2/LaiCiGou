# coding = utf-8
import requests
import json
import time
import traceback

from cfg import COOKIE as cookie
from cfg import PASSWORD as password
from cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from encrypt import sha256
from encrypt import rsa_encrypt
from logger import log
from sale import Sale
from shelf import Shelf
from lai_ci_gou import LaiCiGou
# from ml.captcha_crack_baidu.captcha_crack import Crack
from ml.captcha_recognize.captcha_recognize_new import Crack


class Breed(LaiCiGou):
    def __init__(self, cookie):
        super(Breed, self).__init__(cookie)

        self.crack = Crack()

    # 获取验证码和种子
    def get_captcha_and_seed(self):
        url = 'https://pet-chain.baidu.com/data/captcha/gen'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            log('获取验证码失败：{0}'.format(response['errorMsg']))
            return None, None

        return response['data']['seed'], response['data']['img']

    # 繁殖请求
    def create(self, father_pet_id, mother_pet_id, amount, captcha, seed):
        url = 'https://pet-chain.baidu.com/data/txn/breed/create'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        data = {
            "petId": father_pet_id,
            "senderPetId": mother_pet_id,
            "amount": amount,
            "captcha": captcha,
            "seed": seed,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] == '00':
            log('繁育下单成功')
        else:
            log('繁育下单失败: {0}'.format(response['errorMsg']))

        return response

    def confirm(self, order_id, nonce):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/chooseMyDog?appId=1&tpl='
        secret = sha256(password) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 4,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] == '00':
            log('繁育确认成功')
        else:
            log('繁育确认失败: {0}'.format(response['errorMsg']))

        return response

    # 机器学习破解验证码自动繁育
    def breed(self, father, mother):
        father_id = father['petId']
        mother_id = mother['petId']
        price = father['amount']

        count = 1
        while True:
            log('第{0}次尝试繁殖，父亲狗狗ID：{1}, 母亲狗狗ID: {2}，价格 {3}'.format(count, father_id, mother_id, price))
            count += 1

            seed, img = self.get_captcha_and_seed()
            if not seed:
                time.sleep(3)
                continue

            captcha = self.crack.predict(img)
            response = self.create(father_id, mother_id, price, captcha, seed)

            if response['errorNo'] == '00':
                order_id = response['data']['orderId']
                nonce = response['data']['nonce']
                response = self.confirm(order_id, nonce)
                if response['errorNo'] == '00':
                    return response

            # 10002: 有人抢先下单啦
            # 10018：您今日交易次数已超限，明天再试试吧
            #      : 狗狗已经下架啦
            # TODO 添加错误码到列表
            errors = ['10002', '10018']
            if response['errorNo'] in errors:
                return response

            time.sleep(3)

    # 获取指定稀有属性数量的狗狗
    def get_parents(self, father_rare_num, mother_rare_num):
        father, mother = None, None
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                if pet['isCooling'] or pet['lockStatus'] == 1:
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                rare_num = self.get_rare_amount(pet_info['attributes'])

                if not father and father_rare_num == rare_num:
                    father = pet
                    log('选中狗狗父亲：{0}'.format(father['petId']))
                    continue

                if not mother and mother_rare_num == rare_num:
                    mother = pet
                    log('选中狗狗母亲：{0}'.format(mother['petId']))
                    break
            father_id = father['petId'] if father else None
            mother_id = mother['petId'] if mother else None
            log('第{0}页时： 狗狗父亲 {1}， 狗狗母亲 {2}'.format(page_no, father_id, mother_id))
            if father and mother:
                break
            time.sleep(5)

        return (father, mother)

    # 查询满足繁育条件的狗狗双亲
    # 如果双亲上架状态条件不满足，则处理使之符合条件
    def prepare_parents(self, father_rare_num, father_price, mother_rare_num):
        while True:
            try:
                father, mother = self.get_parents(father_rare_num, mother_rare_num)
                if not father or not mother:
                    log('无满足条件的繁育双亲， 一分钟后重试')
                    time.sleep(60)
                    continue

                # 未上架繁育，将其上架
                if father['shelfStatus'] == 0:
                    log('父亲狗狗{0}处于未上架繁育状态，将其上架'.format(father['petId']))
                    shelf = Shelf(self.cookie)
                    shelf.shelf(father['petId'], father_price)

                    # 等待3分钟避免错误：专属分享，3分钟后可购买
                    time.sleep(3 * 60)
                # 出售中，将其下架然后上架繁育
                elif father['shelfStatus'] == 1:
                    log('父亲狗狗{0}处于售卖中, 将其下架， 三分钟后再挂出繁育'.format(father['petId']))
                    sale = Sale(self.cookie)
                    sale.unsale(father['petId'])

                    # 3分钟后再挂出繁育，避免上下架过频繁
                    time.sleep(3 * 60)

                    log('挂出繁育父亲狗狗{0}'.format(father['petId']))
                    shelf = Shelf(self.cookie)
                    shelf.shelf(father['petId'], father_price)

                # 出售中，将其下架
                if mother['shelfStatus'] == 1:
                    log('母亲狗狗{0}处于出售状态，将其下架然'.format(mother['petId']))
                    sale = Sale(self.cookie)
                    sale.unsale(mother['petId'])
                # 挂出繁育中，将其下架
                elif mother['shelfStatus'] == 2:
                    log('母亲狗狗{0}处于挂出繁育状态，将其下架'.format(mother['petId']))
                    shelf = Shelf(self.cookie)
                    shelf.off_shelf(mother['petId'])

                # 再次获取狗狗双亲信息，保证信息是最新的
                father = self.get_pet_info_on_market(father['petId'])
                mother = self.get_pet_info_on_market(mother['petId'])

                return (father, mother)
            except:
                traceback.print_exc()

    # 狗狗内部繁殖，直到达到当日最大交易次数为止
    def breed_until_max_trade_times(self, father_rare_num, father_price, mother_rare_num):
        while True:
            try:
                father, mother = self.prepare_parents(father_rare_num, father_price, mother_rare_num)
                response = self.breed(father, mother)

                # 10018：您今日交易次数已超限，明天再试试吧
                if response['errorNo'] == '10018':
                    return

                time.sleep(5)
            except:
                time.sleep(5)
                traceback.print_exc()


if __name__ == '__main__':
    breed = Breed(cookie)
    breed.breed_until_max_trade_times(4, 500, 4)
