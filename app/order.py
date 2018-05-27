# coding = utf-8
import requests
import json
import time
from cfg import COOKIE as cookie
from logger import log
from lai_ci_gou import LaiCiGou
from app.db.mongo import db


class Order(LaiCiGou):
    def __init__(self, cookie, clear=True):
        super(Order, self).__init__(cookie)

        self.orders = db['orders']
        self.calculus_coll = db['calculus']

        self.status = {
            1: "已卖出",
            2: "已买入",
            3: "繁育收入",
            4: "繁育支出"
        }

        self.txnStatus = {
            0: "上链中",
            1: "上链中",
            2: "成功",
            3: "失败",
            4: "失败"
        }

        if (clear):
            # 查询保存前先清掉所有数据
            log('强制更新数据，清除所有记录')
            self.orders.delete_many({})
            # 清除微积分数据
            log('强制更新数据，清除微积分总数记录')
            self.calculus_coll.delete_many({})

    # 获取当前微积分总数
    def get_save_latest_calculus(self):
        url = 'https://pet-chain.baidu.com/data/user/get'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        self.calculus_coll.insert({'amount': float(response['data']['amount'])})
        return float(response['data']['amount'])

    # 获取账号交易历史记录数据
    def _get_order_data(self, page_no, page_size, page_total, total_count):
        url = 'https://pet-chain.baidu.com/data/user/order/list'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": page_size,
            "pageTotal": page_total,
            "totalCount": total_count,
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": ""
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        return response['data']

    # 获取交易历史记录总数
    def get_order_count(self):
        return self._get_order_data(1, 10, -1, 0)['totalCount']

    # 分页获取交易历史记录数据
    def get_order_list(self, page_no, page_size, page_total, total_count):
        return self._get_order_data(page_no, page_size, page_total, total_count)['dataList']

    # 保存交易记录简略信息
    def save_order(self, order):
        self.orders.insert({
            "amount": order['amount'],
            "type": order['status'],
            'txnStatus': order['txnStatus'],
            "transDate": order['transDate']}
        )

    # 获取所有交易历史记录数据
    def get_save_all_order(self):
        page_size = 10
        total = self.get_order_count()
        pages = total // page_size if total % page_size == 0 else (total // page_size + 1)
        for page_no in range(pages):
            page_no = page_no + 1
            orders = self.get_order_list(page_no, page_size, pages, total)
            for order in orders:
                self.save_order(order)
                log('保存订单：{0} {1} 微积分 状态 {2}'.format(self.status[order['status']], order['amount'],
                                                     self.txnStatus[order['txnStatus']]))
            time.sleep(1)


if __name__ == '__main__':
    order = Order(cookie)
    order.get_save_latest_calculus()
    order.get_save_all_order()
