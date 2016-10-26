# encoding: utf-8

import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send(receiver, content):
    sender = 'fanying_yt@163.com'
    passwd = 'fy1259680'

    msg = MIMEMultipart()
    msg['to'] = receiver
    msg['from'] = sender

    today = datetime.date.today()
    msg['subject'] = today.strftime('%Y-%m-%d') + '：SAR图请求'

    txt = MIMEText(content,'plain','UTF-8')
    msg.attach(txt)

    try:
        smtp = smtplib.SMTP()
        smtp.connect('smtp.163.com')
        smtp.login(sender, passwd)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
    except smtplib.SMTPException:
        print "Error: 无法发送邮件"

if __name__ == '__main__':
    receive = '707949748@qq.com'
    content = 'test'
    send(receive, content)