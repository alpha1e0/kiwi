#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''

import os
import time
import json
import sqlite3

from collections import OrderedDict
from exception import IssueFormatError
from exception import DatabaseError
from constant import High, Medium, Low, Info
from constant import New, Old, Falsep



class Issue(dict):
    ATTRIBUTES = ['ID', 'name', 'scope', 'severity', 'confidence',
        'references', 'pattern', 'filename', 'lineno', 'context',
        'status', 'comment']


    def __init__(self, **kwargs):
        '''
        @params:
            ID:         检测漏洞使用的规则ID
            name:       检测漏洞使用的规则名称
            scope:      scope信息
            severity:   [High|Medium|Low|Info]
            confidence: [High|Medium|Low]
            references: 漏洞相关介绍信息链接地址
            pattern:    漏洞匹配的pattern
            filename:   漏洞涉及的文件的位置
            lineno:     漏洞所在的行号
            context:    漏洞上下文信息
            status:     [New|Old|Falsep] 漏洞状态标记
            comment:    备注信息
        '''
        for item in kwargs:
            if item not in self.ATTRIBUTES:
                raise IssueFormatError('Key {0} is not allowed for Issue'.\
                    format(item))

        if 'severity' not in kwargs:
            kwargs['severity'] = Info

        if 'confidence' not in kwargs:
            kwargs['confidence'] = Low

        if 'status' not in kwargs:
            kwargs['status'] = New

        super(Issue, self).__init__(kwargs)


    def __setitem__(self, key, value):
        if key not in self.ATTRIBUTES:
            raise IssueFormatError('Key {0} is not allowed for Issue'.\
                    format(item))
        else:
            super(Issue, self).__setitem__(key, value)


    def __getattr__(self, key):
        if key in self.ATTRIBUTES:
            return self.get(key, None)
        else:
            super(Issue, self).__getitem__(key)



def dict_factory(cursor, row):
    '''
    将元祖类型的sql查询结果转换为字典类型
    '''
    result = {}

    for idx, col in enumerate(cursor.description):
        result[col[0]] = row[idx]
        
    return result


class IssueDatabase(object):
    '''
    Issue数据库操作类
    '''
    def __init__(self, dbname):
        self._dbname = dbname
        self._con = None
        self._cur = None

        if os.path.exists(self._dbname):
            self._connect()
        else:
            self._create()


    def _sql(self, *args):
        '''
        执行原始sql语句，用于创建／删除等操作
        '''
        try:
            self._con.execute(*args)
            self._con.commit()
        except sqlite3.Error as error:
            raise DatabaseError("execute sql command {0} error, reason: {1}".\
                format(args[0], str(error)))


    def _query(self, *args):
        '''
        执行sql语句，用于查询
        '''
        try:
            self._cur.execute(*args)
        except IOError as error:
            raise DatabaseError("execute sql query {0} error, reason: {1}".\
                format(args[0], str(error)))

        return self._cur.fetchall()


    def _connect(self):
        try:
            self._con = sqlite3.connect(self._dbname)
            self._con.row_factory = dict_factory
            self._cur = self._con.cursor()
        except sqlite3.Error as error:
            raise DatabaseError("create database {0} error, reason: {1}".\
                format(self._dbname, str(error)))


    def _create(self):
        '''
        创建数据库和Issues表
        '''
        self._connect()

        create_info_table_cmd = ("create table if not exists Info("
            "directory nchar(512),"
            "scan_time nchar(64),"
            "scope_titles nchar(1024),"
            "scope_contents nchar(1024))")

        self._sql(create_info_table_cmd)

        create_issue_table_cmd = ("create table if not exists Issues("
            "id integer primary key autoincrement,"
            "issueid nchar(128),"
            "name nchar(512),"
            "scope nchar(64),"
            "severity integer,"
            "confidence integer,"
            "reference nchar(512),"
            "pattern nchar(128),"
            "filename nchar(512),"
            "lineno integer,"
            "context ntext,"
            "status integer,"
            "comment ntext)")

        self._sql(create_issue_table_cmd)


    def record_scan_info(self, directory, scope_titles, scope_contents):
        insert_info_cmd = ("insert into Info(directory, scan_time, "
            "scope_titles, scope_contents) "
            "values(?, ?, ?, ?)")

        self._sql(insert_info_cmd, (
            os.path.realpath(directory).rstrip("/"),
            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            str(scope_titles),
            str(scope_contents)
            ))


    def encode_code_context(self, context):
        '''
        将列表形式的code context形式转换为字符串以方便存储
        '''
        result = []

        for lineno, line in context:
            result.append("{lineno}:{line}".format(
                lineno=lineno,
                line=line.strip()))

        return "\n".join(result)


    def decode_code_context(self, str_context):
        '''
        将字符串形式的code context转换为列表
        '''
        pattern = re.compile(r"(\d+):(.+)")

        result = []
        for line in str_context.split("\n"):
            match = pattern.match(line)
            if match:
                result.append((match.group(1), match.group(2)))

        return result


    def add_issue(self, issue):
        insert_cmd = ("insert into Issues(issueid, name, scope, severity, "
            "confidence, reference, pattern, filename, lineno, "
            "context, status, comment) values(?, ?, ?, ?, ?, ?, ?, ?, ?,"
            " ?, ?, ?)")

        self._sql(insert_cmd, (
            str(issue.ID), 
            str(issue.name),
            json.dumps(issue.scope),
            issue.severity,
            issue.confidence,
            str(issue.references),
            str(issue.pattern),
            str(issue.filename),
            issue.lineno,
            json.dumps(issue.context),
            issue.status,
            str(issue.comment)))


    def get_issues(self):
        query_cmd = "select * from Issues"

        return self._query(query_cmd)


    def get_classfied_issues(self):
        '''
        获取分类之后的issues
        '''
        new_issues = self._query("select * from Issues where status={0}"\
            .format(New))

        old_issues = self._query("select * from Issues where status={0}"\
            .format(Old))

        falsep_issues = self._query("select * from Issues where status={0}"\
            .format(Falsep))

        return (new_issues, old_issues, falsep_issues)


    def get_scan_info(self):
        query_cmd = "select * from Info"

        return self._query(query_cmd)


    def modify(self, id, status=None, comment=""):
        if status is None:
            modify_cmd = ("update Issues set "
                "comment=? where id=?")
            self._sql(modify_cmd, (comment, id))
        else:
            modify_cmd = ("update Issues set status=?,"
                "comment=? where id=?")
            self._sql(modify_cmd, (status, comment, id))


    def statistics(self):
        severity_info = OrderedDict()

        severity_info[High] = self._query(
            "select COUNT(*) as c from Issues where severity=?", (High,))\
            [0]['c']
        severity_info[Medium] = self._query(
            "select COUNT(*) as c from Issues where severity=?", (Medium,))\
            [0]['c']
        severity_info[Low] = self._query(
            "select COUNT(*) as c from Issues where severity=?", (Low,))\
            [0]['c']
        severity_info[Info] = self._query(
            "select COUNT(*) as c from Issues where severity=?", (Info,))\
            [0]['c']

        status_info = OrderedDict()
        status_info[New] = self._query(
            "select COUNT(*) as c from Issues where status=?", (New,))\
            [0]['c']
        status_info[Old] = self._query(
            "select COUNT(*) as c from Issues where status=?", (Old,))\
            [0]['c']
        status_info[Falsep] = self._query(
            "select COUNT(*) as c from Issues where status=?", (Falsep,))\
            [0]['c']

        return severity_info, status_info



class IssueManager(list):
    '''
    issue管理器
    '''
    def add(self, **kwargs):
        issue = Issue(**kwargs)

        self.append(issue)


    def add_senfile(self, filename, scope, pattern):
        self.add(
            ID = "SENTIVE FILE",
            name = "Sensitive file",
            scope = scope,
            severity = Low,
            confidence = Low,
            pattern = pattern.pattern,
            filename = filename,
            lineno = "0",
            context = []
            )


    def statistics(self):
        result = OrderedDict()
        result[High] = 0
        result[Medium] = 0
        result[Low] = 0
        result[Info] = 0

        for issue in self:
            if issue['severity'] == High:
                result[High] += 1
            elif issue['severity'] == Medium:
                result[Medium] += 1
            elif issue['severity'] == Low:
                result[Low] += 1
            elif issue['severity'] == Info:
                result[Info] += 1

        return result



issuemgr = IssueManager()


