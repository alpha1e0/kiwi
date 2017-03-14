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
            ID
            name:
            scope:
            severity:
            confidence:
            references:
            pattern:
            filename:
            lineno:
            context:
        '''
        super(Issue, self).__init__(kwargs)



    def _format_context(self):
        result = ""

        largest_lineno = self['context'][-1][0]
        no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"

        for line in self['context']:
            if line[0] == self['lineno']:
                result = result + no_fmt.format(str(line[0])) + ": " +\
                    line[1].rstrip() + "\n"
            else:
                result = result + no_fmt.format(str(line[0])) + "- " +\
                    line[1].rstrip() + "\n"

        return result


    def totext(self):
        template = ("--------------------------------\n"
            "[{id}:{name}]\n"
            "<Match:{pattern}> <Severity:{severity}> "
            "<Confidence:{confidence}>\n"
            "@{filename}\n"
            "{context}\n")

        return template.format(
            id = self['ID'],
            name = self['name'],
            pattern = self['pattern'],
            severity = self['severity'],
            confidence = self['confidence'],
            filename = self['filename'],
            context = self._format_context())


    def to_console_text(self):
        return self.totext()


    def tohtml(self):
        return ""



class IssueManager(object):
    '''
    issue管理器
    '''
    def __init__(self):
        self._issues = []
        self._senfiles = []


    def __iter__(self):
        return iter(self._issues)


    @property
    def senfiles(self):
        return self._senfiles


    def add(self, **kwargs):
        issue = Issue(**kwargs)

        self._issues.append(issue)


    def add_senfile(self, filename):
        self._senfiles.append(filename)


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


