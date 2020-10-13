""" custom base64 encoding """

import typing
import math
import re

_keyStr = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/="


def encode(_input: typing.AnyStr = '') -> typing.AnyStr:
    """ encode into base64 """

    if _input == '':
        return ''

    i = 0
    output = ''
    _input = _utf8_encode(_input)

    while i < len(_input):
        chr1 = ord(_input[i]); i += 1
        chr2 = ord(_input[i]); i += 1
        chr3 = ord(_input[i]); i += 1
        enc1 = chr1 >> 2
        enc2 = ((chr1 & 3) << 4) | (chr2 >> 4)
        enc3 = ((chr2 & 15) << 2) | (chr3 >> 6)
        enc4 = chr3 & 63

        if math.isnan(chr2):
            enc3 = enc4 = 64

        elif math.isnan(chr3):
            enc4 = 64

        output += _keyStr[enc1] + _keyStr[enc2] + _keyStr[enc3] + _keyStr[enc4]

    return output[4:5] + output


def decode(_input: typing.AnyStr = '') -> typing.AnyStr:
    """ decode from base64 """

    if _input == '':
        return ''

    i = 0
    output = ''
    _input = re.sub(r'/[^A-Za-z0-9\+\/\=]/', '', _input[1:])
    str_len = len(_input)

    while i < str_len:
        enc1 = _keyStr.index(_input[i]); i += 1
        enc2 = _keyStr.index(_input[i]); i += 1
        enc3 = _keyStr.index(_input[i]); i += 1
        enc4 = _keyStr.index(_input[i]); i += 1

        chr1 = (enc1 << 2) | (enc2 >> 4)
        chr2 = ((enc2 & 15) << 4) | (enc3 >> 2)
        chr3 = ((enc3 & 3) << 6) | enc4

        output = output + chr(chr1)

        if enc3 != 64:
            output = output + chr(chr2)

        if enc4 != 64:
            output = output + chr(chr3)

    output = _utf8_decode(output)

    return output


def _utf8_decode(utftext: typing.AnyStr) -> typing.AnyStr:
    string = ''
    i = 0
    str_len = len(utftext)

    while i < str_len:
        char_code = ord(utftext[i])

        if char_code < 128:
            string += chr(char_code); i += 1

        elif (char_code > 191) and (char_code < 224):
            char_code_2 = ord(utftext[i + 1])
            string += chr(((char_code & 31) << 6) | (char_code_2 & 63))
            i += 2

        else:
            char_code_2 = ord(utftext[i + 1])
            char_code_3 = ord(utftext[i + 2])
            string += chr(((char_code & 15) << 12) | ((char_code_2 & 63) << 6) | (char_code_3 & 63))
            i += 3

    return string


def _utf8_encode(string: typing.AnyStr) -> typing.AnyStr:
    string = re.sub(r'/\r\n/', '\n', string)
    utftext = ''
    str_len = len(string)
    n = 0

    while n < str_len:
        c = ord(string[n])

        if c < 128:
            utftext += chr(c)

        elif (c > 127) and (c < 2048):
            utftext += chr((c >> 6) | 192)
            utftext += chr((c & 63) | 128)

        else:
            utftext += chr((c >> 12) | 224)
            utftext += chr(((c >> 6) & 63) | 128)
            utftext += chr((c & 63) | 128)

        n += 1

    return utftext