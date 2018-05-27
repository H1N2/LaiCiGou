# coding = utf-8
import requests
import json
import time

from cfg import COOKIE as cookie
from cfg import PASSWORD as password
from cfg import BAIDU_PUBLIC_KEY as baidu_pub_key
from encrypt import sha256
from encrypt import rsa_encrypt
from logger import log
from lai_ci_gou import LaiCiGou


class Shelf(LaiCiGou):
    def __init__(self, cookie):
        super(Shelf, self).__init__(cookie)

        self.rare_degree_dic = {0: '普通', 1: '稀有', 2: '卓越', 3: '史诗', 4: '神话', 5: '传说'}

    # 挂出繁育单条狗
    def create(self, pet_id, price):
        url = 'https://pet-chain.baidu.com/data/market/breed/shelf/create'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "petId": pet_id,
            "amount": str(price),
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            log('创建单子失败：{0}'.format(response['errorMsg']))
            return None, None

        return response['data']['orderId'], response['data']['nonce']

    def confirm(self, pet_id, order_id, nonce):
        url = 'https://pet-chain.baidu.com/data/order/confirm'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        secret = sha256(password) + '|' + order_id + '|' + nonce
        secret = rsa_encrypt(baidu_pub_key, secret)
        data = {
            "appId": 1,
            'confirmType': 3,
            "s": secret,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            log('挂出繁育失败: {0}'.format(response['errorMsg']))

        return response

    # 挂出繁育
    def shelf(self, pet_id, price):
        order_id, nonce = self.create(pet_id, price)
        if order_id:
            self.confirm(pet_id, order_id, nonce)

    # 取消繁育
    def off_shelf(self, pet_id):
        url = 'https://pet-chain.baidu.com/data/market/breed/offShelf'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/detail?channel=center&petId=' + pet_id + '&appId=1&tpl='
        data = {
            "appId": 1,
            'petId': pet_id,
            "requestId": int(time.time() * 1000),
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            log('繁育下架失败: {0}'.format(response['errorMsg']))

        return response

    # 按条件挂出繁育所有的狗
    def shelf_by_rare_num(self, rare_num, price):
        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            log('处理第{0}页：'.format(page_no))
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                if pet['isCooling'] or pet['lockStatus'] == 1:
                    continue

                pet_info = self.get_pet_info_on_market(pet['petId'])
                pet_rare_num = self.get_rare_amount(pet_info['attributes'])
                if pet_rare_num != rare_num:
                    continue

                if pet['shelfStatus'] == 0:
                    log('挂出繁育 {0}，{1}稀，价格 {2}'.format(pet['petId'], rare_num, price))
                    self.shelf(pet['petId'], price)

            time.sleep(5)

    # 按稀有属性数量批次挂出繁育，时间上会成倍增加，如不需按稀有数量批次上架请使用shelf_by_rare_num_once
    def shelf_by_rare_nums(self, rare_num_price_dic=None):
        for rare_num in rare_num_price_dic:
            self.shelf_by_rare_num(rare_num, rare_num_price_dic[rare_num])

    # 按稀有属性数量一次性挂出繁育所有的狗
    def shelf_by_rare_nums_once(self, rare_num_price_dic=None):
        if rare_num_price_dic is None:
            log('没有设置价格字典！')
            return

        page_size = 10
        total = self.get_pets_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            log('处理第{0}页：'.format(page_no))
            pets = self.get_pets(page_no, page_size, pages, total)
            for pet in pets:
                if pet['isCooling'] or pet['lockStatus'] == 1:
                    continue
                time.sleep(3)
                pet_info = self.get_pet_info_on_market(pet['petId'])
                rare_num = self.get_rare_amount(pet_info['attributes'])
                if rare_num not in rare_num_price_dic:
                    continue

                price = rare_num_price_dic[rare_num]
                if pet['shelfStatus'] == 0:
                    log('挂出繁育 {0}，{1}稀，价格 {2}'.format(pet['petId'], rare_num, price))
                    order_id, nonce = self.create(pet['petId'], price)
                    if order_id:
                        self.confirm(pet['petId'], order_id, nonce)

            time.sleep(5)


if __name__ == '__main__':
    shelf = Shelf(cookie)
    # rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500, 5: 10000}
    rare_num_price_dic = {0: 100, 1: 100, 2: 100, 3: 100, 4: 500}
    # 按稀有属性数量批次挂出繁育，时间上会成倍增加，如不需按稀有数量批次上架请使用shelf_by_rare_num_once
    # shelf.shelf_by_rare_nums(rare_num_price_dic)
    # 按稀有属性数量一次性挂出繁育所有的狗
    shelf.shelf_by_rare_nums_once(rare_num_price_dic)
