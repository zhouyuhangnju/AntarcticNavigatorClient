# encoding: utf-8

import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from mailutil import getemailpsw

def send(receiver, subject):
    sender, passwd = getemailpsw(0)
    sender = sender + '@lamda.nju.edu.cn'

    msg = MIMEMultipart()
    msg['to'] = receiver
    msg['from'] = sender

    # today = datetime.date.today()
    # msg['subject'] = today.strftime('%Y-%m-%d') + '：SAR图请求'
    msg['subject'] = subject

    txt = MIMEText('南极项目','plain','UTF-8')
    msg.attach(txt)
    # smtp = smtplib.SMTP()
    # smtp.connect('smtp.163.com')
    # smtp.login(sender, passwd)
    # smtp.sendmail(sender, receiver, msg.as_string())
    # smtp.quit()
    # return True
    try:
        smtp = smtplib.SMTP_SSL()
        smtp.connect('210.28.132.67', 465)
        smtp.ehlo()
        smtp.login(sender, passwd)
        smtp.sendmail(sender, receiver, msg.as_string())
        smtp.quit()
        print('send success')
        return True
    except Exception, e:
        print "Error: 无法发送邮件"
        return False




if __name__ == '__main__':
    receive = '1584743373@qq.com'
    content = '[south]'
    send(receive, content)