#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''

from collections import OrderedDict 



class Issue(dict):
    def __init__(self, **kwargs):
        '''
        @params:
            ID:         检测漏洞使用的规则ID
            name:       检测漏洞使用的规则名称
            scope:      scope信息
            severity:   ['High'|'Medium'|'Low'|'Info']
            confidence: ['High'|'Medium'|'Low'|'Info']
            references: 漏洞相关介绍信息链接地址
            pattern:    漏洞匹配的pattern
            filename:   漏洞涉及的文件的位置
            lineno:     漏洞所在的行号
            context:    漏洞上下文信息
        '''
        super(Issue, self).__init__(kwargs)



class IssueManager(object):
    '''
    issue管理器
    '''
    def __init__(self):
        self._issues = []


    def __iter__(self):
        return iter(self._issues)


    def add(self, **kwargs):
        issue = Issue(**kwargs)

        self._issues.append(issue)


    def add_senfile(self, filename, scope, pattern):
        issuemgr.add(
            ID = "SENTIVE FILE",
            name = "Sensitive file",
            scope = scope,
            severity = "Low",
            confidence = "Low",
            pattern = pattern.pattern,
            filename = filename,
            lineno = "0",
            context = []
            )


    def statistics(self):
        result = OrderedDict()
        result['High'] = 0
        result['Medium'] = 0
        result['Low'] = 0
        result['Info'] = 0

        for issue in self._issues:
            if issue['severity'] == 'High':
                result['High'] += 1
            elif issue['severity'] == 'Medium':
                result['Medium'] += 1
            elif issue['severity'] == 'Low':
                result['Low'] += 1
            elif issue['severity'] == 'Info':
                result['Info'] += 1

        return result



issuemgr = IssueManager()


