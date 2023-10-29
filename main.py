# -*- coding: utf8 -*-
import json
from email.mime.multipart import MIMEMultipart

import requests
import datetime
import base64
from Crypto.Cipher import PKCS1_v1_5 as Cipher_pksc1_v1_5
from Crypto.PublicKey import RSA

import smtplib
from smtplib import SMTP_SSL
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from email.mime.application import MIMEApplication # 用于添加附件

num=-1
# #服务器加这句话
# import sys
# reload(sys)
# sys.setdefaultencoding('utf8')

def encrypt(password, public_key):
    rsakey = RSA.importKey(public_key)
    cipher = Cipher_pksc1_v1_5.new(rsakey)
    cipher_text = base64.b64encode(cipher.encrypt(password.encode()))
    return cipher_text.decode()

#第一个参数收件人，第二个参数正文
def send_email(receiver,mail_content):
    host_server = 'smtp.qq.com'  #qq邮箱smtp服务器，需要手动开服务
    sender_qq = 'XXXXXXXXXXXX' #发件人邮箱，即刚才开了服务的邮箱，手动填
    pwd = 'XXXXXXXXXX' #smtp授权码，同上，手动填
    mail_title = 'Successfully booked a seat in the library of GZHU.' #邮件标题
    msg = MIMEMultipart()
    msg["Subject"] = Header(mail_title,'utf-8')
    msg["From"] =sender_qq
    msg["To"] = Header("only you","utf-8")
    msg.attach(MIMEText(mail_content,'plain','utf-8'))


    try:
        smtp = SMTP_SSL(host_server) # ssl登录连接到邮件服务器
        #smtp.set_debuglevel(1) # 0是关闭，1是开启debug
        smtp.ehlo(host_server) # 跟服务器打招呼，告诉它我们准备连接，最好加上这行代码
        smtp.login(sender_qq,pwd)
        smtp.sendmail(sender_qq,receiver,msg.as_string())
        smtp.quit()
        print("邮件发送成功")
    except smtplib.SMTPException:
        print("无法发送邮件")



class GZHU(object):
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.client = requests.session()
        self.client.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:94.0) Gecko/20100101 Firefox/94.0',
        })
        self.url = {
            'scancode': 'http://libbooking.gzhu.edu.cn/scancode.html#/login?sta=1&sysid=1EW&lab=69&type=1',
            'user_info': 'http://libbooking.gzhu.edu.cn/ic-web/auth/userInfo',
            '101': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100647013&resvDates=20220416&sysKind=8',
            '103': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100647014&resvDates=20220416&sysKind=8',
            '202': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100586595&resvDates=20220416&sysKind=8',
            '2C': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100647017&resvDates=20220416&sysKind=8',
            '406': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100586647&resvDates=20220416&sysKind=8',
            '514': 'http://libbooking.gzhu.edu.cn/ic-web/reserve?roomIds=100589684&resvDates=20220416&sysKind=8',
        }

    def loginLib(self, select_room):
        """
        :param select_room: '101’ or '103'
        :return:
        """
        self.client.headers.update({
            'Referer': 'http://libbooking.gzhu.edu.cn/',
            'Host': 'libbooking.gzhuedu.cn'
        })

        # 获得publicKey
        r1 = self.client.get('http://libbooking.gzhu.edu.cn/ic-web/login/publicKey')
        print(r1)
        key = json.loads(r1.text)['data']
        publicKey = key['publicKey']
        nonceStr = key['nonceStr']
        psd = '{};{}'.format(self.password, nonceStr)
        print(r1)

        public_key = '-----BEGIN PUBLIC KEY-----\n' + publicKey + '\n-----END PUBLIC KEY-----'
        password = encrypt(psd, public_key)
        print('password:', password)

        login_data = {
           "bind": 0,
           "logonName": self.username,
           "password": password,
           "type": "",
           "unionId": ""
        }
        self.client.post('http://libbooking.gzhu.edu.cn/ic-web/phoneSeatReserve/login', json=login_data)
        r3 = self.client.get(self.url['user_info'])
        data = json.loads(r3.text)
        if data['message'] == '查询成功':
            self.client.headers.update({
                'token': data['data']['token']
            })
            print('自习室系统登录成功')
            r4 = self.client.get(self.url[select_room])
            room_data = json.loads(r4.text)
            return room_data, data['data']['accNo']
        else:
            print('自习室系统登录失败')

    def postReserve(self,set_bt,set_et,acc_no, begin_time, end_time, dev_id):
        """
        :param acc_no: 自习室系统识别用户的id，int,len=9
        :param begin_time: 开始时间,str,  '1970-01-01 00:00:00'
        :param end_time: 结束时间,str,  '1970-01-01 00:00:00'
        :param dev_id: 座位id,str, len=9

        :return:
        """
        post_data = {
            "sysKind": 8,
            "appAccNo": acc_no,
            "memberKind": 1,
            "resvMember": [acc_no],
            "resvBeginTime": begin_time,
            "resvEndTime": end_time,
            "testName": "",
            "captcha": "",
            "resvProperty": 0,
            "resvDev": [int(dev_id)],
            "memo": ""
        }
        resp = self.client.post('http://libbooking.gzhu.edu.cn/ic-web/reserve', json=post_data)
        print(json.loads(resp.text)['message'])
        with open('config'+str(num)+'.json', 'r') as fp:
                cfg = json.load(fp)
                receiver=cfg['receiver']
                seat="座位: "+cfg['seat']+"\n"
                time="预约时间段为："+set_bt+"—"+set_et+"\n"
                result="结果："+json.loads(resp.text)['message']
                plain=seat+time+result
                send_email(receiver,plain)



    def reserve(self, acc_no, set_bt, set_et, dev_id):
        the_day_after_tomorrow = datetime.datetime.strftime(datetime.datetime.now() + datetime.timedelta(days=1),
                                                            '%Y-%m-%d')
        bt = '{} {}'.format(the_day_after_tomorrow, set_bt)
        et = '{} {}'.format(the_day_after_tomorrow, set_et)
        print('正在post数据，bt:{bt};et:{et}'.format(bt=bt, et=et))
        self.postReserve(set_bt,set_et,acc_no=acc_no,
                         begin_time=bt,
                         end_time=et,
                         dev_id=dev_id)
        return



def start():
    for i in range(0,1):
        global num
        num=i
        print("正在执行第"+str(num+1)+"个用户")
        with open('config'+str(num)+'.json', 'r') as fp:
                cfg = json.load(fp)
                g = GZHU(cfg['username'], cfg['password'])
                room_datas, accNo = g.loginLib(cfg['room'])
                for task in cfg['habit']:
                    dev_id = ''
                    for data in room_datas['data']:
                        if data["devName"] == task['seat_id']:
                            dev_id = data["devId"]
                            break
                    g.reserve(acc_no=accNo,set_bt=task['bt'],set_et=task['et'],dev_id=dev_id)


print("程序开始")
start()
print("程序结束")









