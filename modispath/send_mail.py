# encoding: utf-8

import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send(receiver, content):
    sender = 'PolarRequestSAR@163.com'
    passwd = 'PolarEmail123'

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
        return True
    except smtplib.SMTPException:
        print "Error: 无法发送邮件"
        return False
