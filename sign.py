# coding = utf-8
import requests
import json
import time

from cfg import COOKIE as cookie
from logger import log
from lai_ci_gou import LaiCiGou


class Sign(LaiCiGou):
    def __init__(self, cookie):
        super(Sign, self).__init__(cookie)

    def get_attribute(self, attributes, name):
        for attribute in attributes:
            if attribute['name'] == name:
                return attribute['value']

    # 创建卖出单子
    def sign(self):
        url = 'https://pet-chain.baidu.com/data/user/sign'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/personal?appId=1&tpl='
        data = {
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        if response['errorNo'] != '00':
            log('签到失败：{0}'.format(response['errorMsg']))

        info = response['data']
        if info['isSigned']:
            log('已签到，获得{0}微，签到次数{1} 累计{2}微'.format(info['signAmount'], info['totalSignTimes'], info['totalSignAmount']))


if __name__ == '__main__':
    sign = Sign(cookie)
    sign.sign()
