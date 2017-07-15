#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import sys
import time
import abc

from commons import conf
from issuemgr import issuemgr



def get_reporter(filename):
    if filename.endswith(".txt"):
        return TextReporter()

    if filename.endswith(".html"):
        return HtmlReporter()

    if filename.endswith(".idb"):
        return DatabaseReporter()

    return TextReporter()



class Reporter(object):
    scope = 'default'
    _WIDTH = 80

    def __init__(self):
        self.banner = self._banner()


    def _banner(self):
        '''
        return banner information
        '''
        fmt = "|{0:^" + "{0}".format(self._WIDTH-2) + "}|"

        banner = "+" + "-" * (self._WIDTH-2) + "+\n"
        banner = banner + fmt.format(
            "BugTrack. Security tool for auditing source code.") + "\n"
        banner = banner + \
            fmt.format("https://github.com/alpha1e0/bugtrack") + "\n"
        banner = banner + "+" + "-" * (self._WIDTH-2) + "+\n"

        return banner


    def report(self, target):
        '''
        输出问题
        '''
        if isinstance(target, basestring):
            with open(target, 'w') as _file:
                self._report(_file)
        else:
            self._report(target)


    def _report(self, fobj):
        pass
        


class TextReporter(Reporter):
    scope = "text"

    def _format_issue_context(self, context):
        result = ""

        largest_lineno = context[-1][0]
        no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"

        for line in context:
            if line[0] == self['lineno']:
                result = result + no_fmt.format(str(line[0])) + ": " +\
                    line[1].rstrip() + "\n"
            else:
                result = result + no_fmt.format(str(line[0])) + "- " +\
                    line[1].rstrip() + "\n"

        return result


    def _format_issue(self, issue):
        template = (
            "[{id}:{name}]\n"
            "<Match:{pattern}> <Severity:{severity}> "
            "<Confidence:{confidence}>\n"
            "@{filename}\n"
            "{context}\n")

        return template.format(
            id = issue['ID'],
            name = issue['name'],
            pattern = issue['pattern'],
            severity = issue['severity'],
            confidence = issue['confidence'],
            filename = issue['filename'],
            context = self._format_issue_context(issue['context']))
    

    def _report(self, fobj):
        template = "{title}\n\n{senfiles}\n\n{issues}\n\n{statistics}"

        title = "{banner}\nScaning <{directory}> at {time}".format(
                banner = self.banner,
                directory = conf.target,
                time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        senfiles = "-"*80 + "\nFound sensitive files as follows:\n\n"
        for filename in issuemgr.senfiles:
            senfiles = senfiles + "@" + filename + "\n"

        issues = "-"*80 + "\nFound security issues as follows:\n\n"
        for issue in issuemgr:
            issues = issues + issue.totext()

        statistics = "-"*80 + "\nStatistics information:\n"
        sinfo = issuemgr.statistics()
        for s in sinfo:
            statistics = statistics + \
                "{key}: {value}".format(key=s, value=sinfo[s]) + "\n"

        content = template.format(
            title=title,
            senfiles = senfiles,
            issues = issues,
            statistics = statistics)

        fobj.write(content)
        fobj.flush()


class ConsoleReporter(TextReporter):
    scope = "console"


class HtmlReporter(Reporter):
    pass


class DatabaseReporter(Reporter):
    pass
