# -*- coding: utf-8 -*-

# 鎵撳崱鑴氫慨鏀硅嚜ZJU-nCov-Hitcarder鐨勫紑婧愪唬鐮侊紝鎰熻阿杩欎綅鍚屽寮€婧愮殑浠ｇ爜

import requests
import json
import re
import datetime
import time
import sys
# import ddddocr

class ClockIn(object):
    """Hit card class

    Attributes:
        username: (str) 娴欏ぇ缁熶竴璁よ瘉骞冲彴鐢ㄦ埛鍚嶏紙涓€鑸负瀛﹀彿锛�
        password: (str) 娴欏ぇ缁熶竴璁よ瘉骞冲彴瀵嗙爜
        LOGIN_URL: (str) 鐧诲綍url
        BASE_URL: (str) 鎵撳崱棣栭〉url
        SAVE_URL: (str) 鎻愪氦鎵撳崱url
        HEADERS: (dir) 璇锋眰澶�
        sess: (requests.Session) 缁熶竴鐨剆ession
    """
    LOGIN_URL = "https://zjuam.zju.edu.cn/cas/login?service=https%3A%2F%2Fhealthreport.zju.edu.cn%2Fa_zju%2Fapi%2Fsso%2Findex%3Fredirect%3Dhttps%253A%252F%252Fhealthreport.zju.edu.cn%252Fncov%252Fwap%252Fdefault%252Findex"
    BASE_URL = "https://healthreport.zju.edu.cn/ncov/wap/default/index"
    SAVE_URL = "https://healthreport.zju.edu.cn/ncov/wap/default/save"
 #   captcha_url = "https://healthreport.zju.edu.cn/ncov/wap/default/code"
    HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36"
    }
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.sess = requests.Session()

    def login(self):
        """Login to ZJU platform"""
        res = self.sess.get(self.LOGIN_URL, headers=self.HEADERS)
        execution = re.search(
            'name="execution" value="(.*?)"', res.text).group(1)
        res = self.sess.get(
            url='https://zjuam.zju.edu.cn/cas/v2/getPubKey', headers=self.HEADERS).json()
        n, e = res['modulus'], res['exponent']
        encrypt_password = self._rsa_encrypt(self.password, e, n)

        data = {
            'username': self.username,
            'password': encrypt_password,
            'execution': execution,
            '_eventId': 'submit'
        }
        res = self.sess.post(url=self.LOGIN_URL, data=data, headers=self.HEADERS)

        # check if login successfully
        if '缁熶竴韬唤璁よ瘉' in res.content.decode():
            raise LoginError('鐧诲綍澶辫触锛岃鏍稿疄璐﹀彿瀵嗙爜閲嶆柊鐧诲綍')
        return self.sess

    def post(self):
        """Post the hitcard info"""
        res = self.sess.post(self.SAVE_URL, data=self.info, headers=self.HEADERS)
        return json.loads(res.text)

    def get_date(self):
        """Get current date"""
        today = datetime.date.today()
        return "%4d%02d%02d" % (today.year, today.month, today.day)

    def get_info(self, html=None):
        """Get hitcard info, which is the old info with updated new time."""
        if not html:
            res = self.sess.get(self.BASE_URL, headers=self.HEADERS)
            html = res.content.decode()
            # 鏂板缓ocr锛屽苟璇诲彇楠岃瘉鐮佽繘琛岃瘑鍒�
     #       ocr = ddddocr.DdddOcr(old=True)
     #       resp = self.sess.get(self.captcha_url, headers=self.HEADERS)
     #       captcha = ocr.classification(resp.content)
        try:
            old_infos = re.findall(r'oldInfo: ({[^\n]+})', html)
            if len(old_infos) != 0:
                old_info = json.loads(old_infos[0])
            else:
                raise RegexMatchError("鏈彂鐜扮紦瀛樹俊鎭紝璇峰厛鑷冲皯鎵嬪姩鎴愬姛鎵撳崱涓€娆″啀杩愯鑴氭湰")

            new_info_tmp = json.loads(re.findall(r'def = ({[^\n]+})', html)[0])
            new_id = new_info_tmp['id']
            name = re.findall(r'realname: "([^\"]+)",', html)[0]
            number = re.findall(r"number: '([^\']+)',", html)[0]
        except IndexError:
            raise RegexMatchError('Relative info not found in html with regex')
        except json.decoder.JSONDecodeError:
            raise DecodeError('JSON decode error')

        new_info = old_info.copy()
        new_info['id'] = new_id
        new_info['name'] = name
        new_info['number'] = number
        new_info["date"] = self.get_date()
        new_info["created"] = round(time.time())
        new_info["address"] = "娴欐睙鐪佹澀宸炲競瑗挎箹鍖�"
        new_info["area"] = "娴欐睙鐪� 鏉窞甯� 瑗挎箹鍖�"
        new_info["province"] = new_info["area"].split(' ')[0]
        new_info["city"] = new_info["area"].split(' ')[1]
        # form change
        new_info['jrdqtlqk[]'] = 0
        new_info['jrdqjcqk[]'] = 0
        new_info['sfsqhzjkk'] = 1   # 鏄惁鐢抽鏉窞鍋ュ悍鐮�
        new_info['sqhzjkkys'] = 1   # 鏉窞鍋ュ悍鍚楅鑹诧紝1:缁胯壊 2:绾㈣壊 3:榛勮壊
        new_info['sfqrxxss'] = 1    # 鏄惁纭淇℃伅灞炲疄
        new_info['jcqzrq'] = ""
        new_info['gwszdd'] = ""
        new_info['szgjcs'] = ""
        
        # add in 2022.07.08
        new_info['sfymqjczrj'] = 2  #鍚屼綇浜哄憳鏄惁鍙戠儹
        new_info['ismoved'] = 4     #鏄惁鏈夌寮€
        new_info['internship'] = 3  #鏄惁杩涜瀹炰範
        new_info['sfcxzysx'] = 2    #鏄惁娑夊強鐤儏绠℃帶
        
   #     new_info['verifyCode'] = captcha
        # 2021.08.05 Fix 2
        magics = re.findall(r'"([0-9a-f]{32})":\s*"([^\"]+)"', html)
        for item in magics:
            new_info[item[0]] = item[1]

        self.info = new_info
        return new_info

    def _rsa_encrypt(self, password_str, e_str, M_str):
        password_bytes = bytes(password_str, 'ascii')
        password_int = int.from_bytes(password_bytes, 'big')
        e_int = int(e_str, 16)
        M_int = int(M_str, 16)
        result_int = pow(password_int, e_int, M_int)
        return hex(result_int)[2:].rjust(128, '0')


# Exceptions
class LoginError(Exception):
    """Login Exception"""
    pass


class RegexMatchError(Exception):
    """Regex Matching Exception"""
    pass


class DecodeError(Exception):
    """JSON Decode Exception"""
    pass


def main(username, password):
    """Hit card process

    Arguments:
        username: (str) 娴欏ぇ缁熶竴璁よ瘉骞冲彴鐢ㄦ埛鍚嶏紙涓€鑸负瀛﹀彿锛�
        password: (str) 娴欏ぇ缁熶竴璁よ瘉骞冲彴瀵嗙爜
    """
    print("\n[Time] %s" %
          datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("馃殞 鎵撳崱浠诲姟鍚姩")

    dk = ClockIn(username, password)

    print("鐧诲綍鍒版禉澶х粺涓€韬唤璁よ瘉骞冲彴...")
    try:
        dk.login()
        print("宸茬櫥褰曞埌娴欏ぇ缁熶竴韬唤璁よ瘉骞冲彴")
    except Exception as err:
        print(str(err))
        raise Exception

    print('姝ｅ湪鑾峰彇涓汉淇℃伅...')
    try:
        dk.get_info()
        print('宸叉垚鍔熻幏鍙栦釜浜轰俊鎭�')
    except Exception as err:
        print('鑾峰彇淇℃伅澶辫触锛岃鎵嬪姩鎵撳崱锛屾洿澶氫俊鎭�: ' + str(err))
        raise Exception

    print('姝ｅ湪涓烘偍鎵撳崱')
    try:
        res = dk.post()
        if str(res['e']) == '0':
            print('宸蹭负鎮ㄦ墦鍗℃垚鍔燂紒')
        else:
            print(res['m'])
            if res['m'].find("宸茬粡") != -1: # 宸茬粡濉姤杩囦簡 涓嶆姤閿�
                pass
            else:
                count = 0
                while (str(res['e']) != '0' and count < 3):
                    time.sleep(5)
                    dk.get_info()
                    res = dk.post()
                    count +=1
                if str(res['e']) == '0':
                    print('宸蹭负鎮ㄦ墦鍗℃垚鍔燂紒')
                else:
                    raise Exception
    except Exception:
        print('鏁版嵁鎻愪氦澶辫触')
        raise Exception


if __name__ == "__main__":
    username = sys.argv[1]
    password = sys.argv[2]
    try:
        main(username, password)
    except Exception:
        exit(1)
