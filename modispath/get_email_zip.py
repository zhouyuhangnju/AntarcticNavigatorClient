#!/usr/bin/env python
# -*- coding: utf-8 -*-
import poplib
import email
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr
import time
import tempfile
import zipfile
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
import base64
from email import encoders
# 输入邮件地址, 口令和POP3服务器地址:
'''
email = input('Email: ')
password = input('Password: ')
pop3_server = input('POP3 server: ')
'''
import imaplib
import re
import mimetypes
import os
import shutil
from optparse import OptionParser

def LoginMail(hostname, user, password):
    r = imaplib.IMAP4_SSL(hostname)
    r.login(user, password)
    x, y = r.status('INBOX', '(MESSAGES UNSEEN)')
    unseennum  = y[0][-2] - 48
    return unseennum


def guess_charset(msg):
    charset = msg.get_charset()
    if charset is None:
        content_type = msg.get('Content-Type', '').lower()
        pos = content_type.find('charset=')
        if pos >= 0:
            charset = content_type[pos + 8:].strip()
    return charset

def decode_str(s):
    value, charset = decode_header(s)[0]
    if charset:
        value = value.decode(charset)
    return value

def print_info(msg, indent=0):
    mark = False
    if indent == 0:
        for header in ['From', 'To', 'Subject']:
            value = msg.get(header, '')
            if value:
                if header=='Subject':
                    value = decode_str(value)
                    # print('subject', value)
                    if value[0:7] == '[south]':
                        l_time = value.split(' ')[2]
                        if os.path.exists('time.txt'):
                            time_log = open('time.txt')
                            if l_time > time_log.readline():
                                mark = True
                            time_log.close()
                        if mark or not os.path.exists('time.txt'):
                            new_log = open('time.txt', 'w')
                            new_log.write(l_time)
                            new_log.close()
                            mark = True
                        # print('longitati', longitati)
                        # mark = True
                else:
                    hdr, addr = parseaddr(value)
                    name = decode_str(hdr)
                    value = u'%s <%s>' % (name, addr)
            # print('%s%s: %s' % ('  ' * indent, header, value))
    if mark:
        counter = 1
        for part in msg.walk():
                 # multipart/* are just containers
                 if part.get_content_maintype() == 'multipart':
                     continue
                 # Applications should really sanitize the given filename so that an
                 # email message can't be used to overwrite important files
                 filename = part.get_filename()
                 if not filename:
                     ext = mimetypes.guess_extension(part.get_content_type())
                     if not ext:
                         # Use a generic bag-of-bits extension
                         ext = '.bin'
                     filename = 'part-%03d%s' % (counter, ext)
                 counter += 1
                 if os.path.exists('download'):
                     shutil.rmtree('download')
                 os.mkdir('download')
                 fp = open(os.path.join('download', filename), 'wb')
                 fp.write(part.get_payload(decode=True))
                 fp.close()

    return None


# 连接到POP3服务器:

def checkemail(user,password,pop3_server,prenum):
	server = poplib.POP3_SSL(pop3_server, '995')
	# 可以打开或关闭调试信息:
	# server.set_debuglevel(1)
	# 可选:打印POP3服务器的欢迎文字:
	# print(time.localtime(time.time()))
	# print(server.getwelcome())
	# 身份认证:
	server.user(user)
	server.pass_(password)
	# stat()返回邮件数量和占用空间:
	# print('Messages: %s. Size: %s' % server.stat())
	# list()返回所有邮件的编号:
	resp, mails, octets = server.list()
	# 可以查看返回的列表类似['1 82923', '2 2184', ...]
	# print(mails)
	# 获取最新一封邮件, 注意索引号从1开始:
	index = len(mails)
	if index == prenum:
		# print 'in'
		# print index
		return index, None

	unseennum = index - prenum
	print('num of mails:', index)
	print('unseennum:', unseennum)
	for j in range(unseennum):
		ii = index - j
		# print(ii)
		try:
		       resp, lines, octets = server.retr(ii)

		       for i in range(len(lines)):

		                 lines[i] = lines[i].decode()

		       mail = email.message_from_string('\n'.join(lines))
		       print_info(mail)

		except Exception as e:
		       # raise('exception:', e)
		       print('exception:', e)
		       continue
	for i in range(index):
		server.dele(i+1)
	server.quit()
	return index,None

if __name__ == '__main__':
    from mailutil import getemailpsw
    user, password = getemailpsw(3)
    user = user + '@lamda.nju.edu.cn'
    pop3_server = '210.28.132.67'
    checkemail(user,password,pop3_server,0)
