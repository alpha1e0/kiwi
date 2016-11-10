#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


class Issue(dict):
    def __init__(self, **kwargs):
        '''
        @params:
            type:
            scope:
            severity:
            confidence:
            information:
            references:
            pattern:
            filename:
            lineno:
            matchs:
        '''
        super(Issue, self).__init__(kwargs)


    def toHtml(self):
        pass

    def toText(self):
        pass


class IssueTable(object):
    def add(self, issue):
        pass

    def delect(self, issueID):
        pass

    def update(self, issue):
        pass

    def query(self, issue):
        pass

    def export(self, orderby):
        pass


class IssueDB(object):
    def __init__(self, dbFile):
        self._dbFile = dbFile


    def create(self):
        pass


    def delete(self):
        pass