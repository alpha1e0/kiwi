#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


High = 1000
Medium = 100
Low = 10
Info = 1

New = 100
Old = 10
Falsep = 1


status_map = {
    100: ('high', u'新漏洞'),
    10: ('medium', u'老漏洞'),
    1: ('low', u'误报漏洞')
}

severity_map = {
    1000: ('high', u"漏洞等级:致命"),
    100: ('medium', u"漏洞等级:严重"),
    10: ('low', u"漏洞等级:一般"),
    1: ('info', u"漏洞等级:提示")
}

confidence_map = {
    1000: ('high', u"确认度:高"),
    100: ('medium', u"确认度:中"),
    10: ('low', u"确认度:低")
}