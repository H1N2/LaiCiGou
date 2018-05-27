# coding = utf-8
import requests
import json
import time
import xmltodict
from cfg import COOKIE as cookie
from logger import log
from lai_ci_gou import LaiCiGou
from app.utils.svg import Svg
from app.db.mongo import db


class AttributeSvgParser(LaiCiGou):
    def __init__(self, cookie, clear=False):
        super(AttributeSvgParser, self).__init__(cookie)

        self.svg = Svg(cookie)

        self.attribute_svgs = db['attribute_svg']

        if (clear):
            # 查询保存前先清掉所有数据
            log('强制更新数据，清除所有记录')
            self.attribute_svgs.delete_many({})

        self.predict_results = {}

        self.predict_fail = []

    def get_pets_on_sale(self, page_no, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/queryPetsOnSale'
        headers = self.headers_template
        data = {
            "pageNo": page_no,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{\"1\":\"" + str(rare_degree) + "\"}",
            "querySortType": "AMOUNT_ASC",
            "petIds": [],
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        pets = response['data']['petsOnSale']
        return pets

    def get_pets_on_breed(self, page_no, rare_degree):
        url = 'https://pet-chain.baidu.com/data/market/breed/pets'
        headers = self.headers_template
        headers['Referer'] = 'https://pet-chain.baidu.com/chain/breedCentre?appId=1&tpl='
        data = {
            "pageNo": page_no,
            "pageSize": 10,
            "lastAmount": "",
            "lastRareDegree": "",
            "filterCondition": "{\"1\":\"" + str(rare_degree) + "\"}",
            "querySortType": "AMOUNT_ASC",
            "petIds": [],
            "requestId": int(time.time() * 1000),
            "appId": 1,
            "tpl": "",
        }
        r = requests.post(url, headers=headers, data=json.dumps(data))
        response = json.loads(r.content)
        pets = response['data']['pets4Breed']
        return pets

    def get_attribute(self, attributes, name):
        for attribute in attributes:
            if attribute['name'] == name:
                return attribute

    # 保存或者更新属性数据
    def save_update_attribute(self, attributes, name, svg_value):
        attribute = self.get_attribute(attributes, name)
        exist = self.attribute_svgs.find_one(attribute)
        if exist:
            self.attribute_svgs.update_one({
                '_id': exist['_id']
            }, {
                '$set': {
                    'svgValue': svg_value
                }
            }, upsert=False)
        else:
            attribute['svgValue'] = svg_value
            self.attribute_svgs.insert(attribute)

    # 按指定稀有度查询狗狗，包括售卖的和挂出繁育的
    def get_save_pet_svg_criteria(self, rare_degree):
        # 当前百度允许查询的最大页数为200
        max_page_no = 200
        sample_count = 0
        for page_no in range(max_page_no):
            page_no = page_no + 1
            log('第{0}页{1}狗狗'.format(page_no, self.rare_degree_dic[rare_degree]))
            # 获取市场上售卖的狗狗
            pets_on_sale = self.get_pets_on_sale(page_no, rare_degree)
            # 获取市场上繁育的狗狗
            pets_on_breed = self.get_pets_on_breed(page_no, rare_degree)
            # 合并市场上售卖和繁育的狗狗
            pets = pets_on_sale + pets_on_breed
            for pet in pets:
                pet_id = pet['petId']
                log('第 {0} 个样本 {1}'.format(sample_count, pet_id))
                sample_count = sample_count + 1
                info = self.get_pet_info_on_market(pet_id)

                svg_xml = self.svg.get_pet_svg(pet_id)
                # print(svg_xml)
                svg_json = xmltodict.parse(svg_xml)

                # 体型
                body_shape = self.svg.get_body_shape(svg_json)
                self.save_update_attribute(info['attributes'], '体型', body_shape)
                # 身体色
                body_color = self.svg.get_body_color(svg_json)
                self.save_update_attribute(info['attributes'], '身体色', body_color)
                # 嘴巴
                nose_mouth = self.svg.get_nose_mouth(svg_json)
                self.save_update_attribute(info['attributes'], '嘴巴', nose_mouth)
                # 花纹
                pattern = self.svg.get_pattern(svg_json)
                self.save_update_attribute(info['attributes'], '花纹', pattern)
                # 花纹色
                pattern_color = self.svg.get_pattern_color(svg_json)
                self.save_update_attribute(info['attributes'], '花纹色', pattern_color)
                # 肚皮色
                tummy_color = self.svg.get_tummy_color(svg_json)
                self.save_update_attribute(info['attributes'], '肚皮色', tummy_color)
                # 眼睛色
                eye_color = self.svg.get_eye_color(svg_json)
                self.save_update_attribute(info['attributes'], '眼睛色', eye_color)
                # 眼睛
                eye_shape = self.svg.get_eye_shape(svg_json)
                self.save_update_attribute(info['attributes'], '眼睛', eye_shape)
            time.sleep(5)

    # 根据svg预测属性值
    def predict_attribute(self, svg_xml, name):
        svg_json = xmltodict.parse(svg_xml)
        svg_value = None
        if name == '体型':
            svg_value = self.svg.get_body_shape(svg_json)
        elif name == '身体色':
            svg_value = self.svg.get_body_color(svg_json)
        elif name == '嘴巴':
            svg_value = self.svg.get_nose_mouth(svg_json)
        elif name == '花纹':
            svg_value = self.svg.get_pattern(svg_json)
        elif name == '花纹色':
            svg_value = self.svg.get_pattern_color(svg_json)
        elif name == '肚皮色':
            svg_value = self.svg.get_tummy_color(svg_json)
        elif name == '眼睛色':
            svg_value = self.svg.get_eye_color(svg_json)
        elif name == '眼睛':
            svg_value = self.svg.get_eye_shape(svg_json)

        attribute = self.attribute_svgs.find_one({'name': name, 'svgValue': svg_value})

        value = attribute['value'] if attribute else None
        rare_degree = ''
        if attribute and attribute['rareDegree']:
            rare_degree = attribute['rareDegree']

        return value, rare_degree

    # 预测单条狗狗的属性， 结果写入self.predict_results及self.predict_fail（如果失败）
    def predict_one_pet(self, pet_id):
        info = self.get_pet_info_on_market(pet_id)
        svg_xml = self.svg.get_pet_svg(pet_id)
        print(svg_xml)
        attributes = ['体型', '身体色', '嘴巴', '花纹', '花纹色', '肚皮色', '眼睛色', '眼睛']
        fail = False
        for attribute in attributes:
            predict, rare_degree = self.predict_attribute(svg_xml, attribute)
            actual = self.get_attribute(info['attributes'], attribute)['value']
            log("{0}预测 {1}， 实际为 {2}".format(attribute, predict, actual))
            correct = predict == actual
            if not correct:
                fail = True

            if attribute in self.predict_results:
                if correct:
                    self.predict_results[attribute]['pass'] = self.predict_results[attribute]['pass'] + 1
                else:
                    self.predict_results[attribute]['fail'] = self.predict_results[attribute]['fail'] + 1
            else:
                if correct:
                    self.predict_results[attribute] = {'pass': 1, 'fail': 0}
                else:
                    self.predict_results[attribute] = {'pass': 0, 'fail': 1}
        if fail:
            self.predict_fail.append(pet_id)

    def predict_one_pet_api(self, pet_id):
        info = self.get_pet_info_on_market(pet_id)
        return self.predict_one_pet_svg_url_api(info['petUrl'])

    # 预测
    def predict_one_pet_svg_url(self, pet_url):
        svg_xml = self.svg.get_pet_svg_xml(pet_url)
        attr_info = '\n'
        attributes = ['体型', '身体色', '嘴巴', '花纹', '花纹色', '肚皮色', '眼睛色', '眼睛']
        for attribute in attributes:
            predict, rare_degree = self.predict_attribute(svg_xml, attribute)
            if predict:
                attr_info = attr_info + "{:\u3000<6} {:\u3000<8} {:>2}".format(attribute, predict, rare_degree) + '\n'
            else:
                attr_info = attr_info + "{:\u3000<6} {:\u3000<8} {:>2}".format(attribute, '（无法识别）', '') + '\n'
        return attr_info

    def predict_one_pet_svg_url_api(self, pet_url):
        svg_xml = self.svg.get_pet_svg_xml(pet_url)
        # attributes = ['体型', '身体色', '嘴巴', '花纹', '花纹色', '肚皮色', '眼睛色', '眼睛']
        attributes = ['体型', '花纹', '眼睛', '眼睛色', '嘴巴', '肚皮色', '身体色', '花纹色']
        results = {}
        for attribute in attributes:
            predict, rare_degree = self.predict_attribute(svg_xml, attribute)
            if predict:
                results[attribute] = '{0} {1}'.format(predict, rare_degree)
            else:
                results[attribute] = '（无法识别） '
        results['petUrl'] = pet_url
        return results

    def predict_pets_until(self, rare_degree, max_test_sample=1000):
        # 当前百度允许查询的最大页数为200
        max_page_no = 200
        sample_count = 0
        for page_no in range(max_page_no):
            page_no = page_no + 1
            log('第{0}页{1}狗狗'.format(page_no, self.rare_degree_dic[rare_degree]))
            # 获取市场上售卖的狗狗
            pets_on_sale = self.get_pets_on_sale(page_no, rare_degree)
            # 获取市场上繁育的狗狗
            pets_on_breed = self.get_pets_on_breed(page_no, rare_degree)
            # 合并市场上售卖和繁育的狗狗
            pets = pets_on_sale + pets_on_breed
            for pet in pets:
                log('第 {0} 个测试样本 {1}'.format(sample_count, pet['petId']))
                sample_count = sample_count + 1
                if sample_count == max_test_sample:
                    log(self.predict_results)
                    log(self.predict_fail)
                    return
                self.predict_one_pet(pet['petId'])

            log(self.predict_results)
            log(self.predict_fail)
            time.sleep(5)


if __name__ == '__main__':
    attribute_svg = AttributeSvgParser(cookie, clear=True)
    attribute_svg.get_save_pet_svg_criteria(4)

    # attribute_svg = AttributeSvgParser(cookie, clear=False)
    # attribute_svg.get_save_pet_svg_criteria(4)

    attribute_svg = AttributeSvgParser(cookie, clear=False)
    attribute_svg.predict_one_pet('2000517220124700486')
    attribute_svg.predict_pets_until(4)
    pass
