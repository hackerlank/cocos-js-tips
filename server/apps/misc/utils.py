#!/usr/bin/env python
# -*- coding: utf-8 -*-

# @Date : 2015-07-15 13:43:20
# @Author : Jiank (http://jiankg.github.com)
# @doc
#   工具
# @end
# @copyright (C) 2015, kimech

import time
import datetime
import hashlib
import ujson
import base64
import logging

from Crypto.Cipher import AES
from libs.pkcs7 import PKCS7Encoder

from torngas.settings_manager import settings

def time_me(fn):
    def _wrapper(*args, **kwargs):
        start = time.time()
        result = fn(*args, **kwargs)
        logging.error("【%s】 cost %.4f ms" % (fn.__name__, (time.time() - start) * 1000))
        logging.error("=" * 60)
        return result

    return _wrapper

def md5(string):
    m = hashlib.md5()
    m.update(string)

    return m.hexdigest()

def bit_test(state, pos):
    return (state >> (pos - 1)) & 1

def bit_set(state, pos):
    return state ^ (1 << (pos - 1))

def bin2dec(string_num):
    """二进制转十进制
    """
    return str(int(string_num, 2))

def dec2bin(string_num):
    """十进制转二进制
    """
    base = [str(x) for x in range(10)] + [ chr(x) for x in range(ord('A'),ord('A')+6)]
    num = int(string_num)
    mid = []
    while True:
        if num == 0: break
        num, rem = divmod(num, 2)
        mid.append(base[rem])

    return ''.join([str(x) for x in mid[::-1]])

def urlencode(str):
    reprStr = repr(str).replace(r'\x', '%')
    return reprStr[1:-1]

def response_json(handler, data):
    return handler.write(ujson.dumps(data))

def merge_child_list(l):
    """
    [[1,2],[2,3]] => [1,2,2,3]
    """
    return reduce(lambda x, y: x.extend(y) or x, [i for i in l])

def check_white_ips(ip, server_info):
    white_ips = server_info.get("white_ips").split(",")
    if server_info.get("game_server_state") != 1:
        return True
    if unicode(ip, 'UTF-8') in white_ips:
        return True
    return False

def is_not_today(timestamp):
    """判断时间戳不是今天
    """
    a = datetime.datetime.utcfromtimestamp(timestamp)

    return a.date() != datetime.date.today()

def today():
    """取得今日的日期

    Return:
        20150819
    """
    return int(time.strftime('%Y%m%d'))

def datestamp(datestring):
    """对应日期零点的时间戳

    Args:
        20151204

    Returns:
        1449205100
    """
    format = "%Y%m%d"
    date = datetime.datetime.strptime(datestring, format)

    return int(date.strftime("%s"))

def timestamp2string(stamp):
    """时间戳转字符串日期类型

    Args:
        1449205100

    Returns:
        20151204
    """
    date = datetime.datetime.fromtimestamp(stamp)
    return date.strftime("%Y%m%d")

def split_date(date):
    """拆分日期

    Args:
        20151110

    Returns:
        (2015, 11, 10)
    """
    year = int(str(date)[:4])
    month = int(str(date)[4:6])
    day = int(str(date)[-2:])

    return (year, month, day)

def printf(**kwargs):
    """测试打印工具
    """
    string = ""
    for key, value in kwargs.iteritems():
        string += "%s : %s || " % (key, value)

    print string

def encrypt(data):
    """通信数据加密
    """
    encoder = PKCS7Encoder()

    encryptor = AES.new(settings.ENCODE_DECODE_KEY, AES.MODE_CBC, settings.ENCODE_DECODE_IV)
    padded_text = encoder.encode(data)
    encrypted_data = encryptor.encrypt(padded_text)

    return base64.b64encode(encrypted_data)

def decrypt(data):
    """通信数据解密
    """
    dencoder = PKCS7Encoder()
    cipher = base64.b64decode(data)
    decryptor = AES.new(settings.ENCODE_DECODE_KEY, AES.MODE_CBC, settings.ENCODE_DECODE_IV)
    plain = decryptor.decrypt(cipher)

    return dencoder.decode(plain)

# 计算文本内容长度
def is_chinese(uchar):
    '''判断一个unicode是否是汉字'''
    if uchar >= u'\u4e00' and uchar<=u'\u9fa5':
        return True
    return False

def is_number(uchar):
    """判断一个unicode是否是数字"""
    if uchar >= u'\u0030' and uchar<=u'\u0039':
        return True
    return False

def is_alphabet(uchar):
    """判断一个unicode是否是英文字母"""
    if (uchar >= u'\u0041' and uchar<=u'\u005a') \
        or (uchar >= u'\u0061' and uchar<=u'\u007a'):
        return True
    return False

def is_other(uchar):
    """判断是否非汉字，数字和英文字符"""
    if not (is_chinese(uchar) or is_number(uchar) or is_alphabet(uchar)):
        return True
    return False

# gbk宽度可用于对齐，中文占两个字符位置
def gbk_word_len(word):
    if is_number(word) or is_alphabet(word):
        return 1
    return 2

# 计算文本显示宽度
def gbk_words_len(unicode_words):
    if type(unicode_words) is not unicode:
        unicode_words = unicode(unicode_words, "utf-8")

    i = 0
    for word in unicode_words:
        i += gbk_word_len(word)

    return i
