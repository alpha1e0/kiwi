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
            fmt.format("https://github.com/alpha1e0/pentestdb") + "\n"
        banner = banner + "+" + "-" * (self._WIDTH-2) + "+\n"

        return banner


    def report(self, issuemgr, fobj, directory):
        '''
        输出问题
        '''
        return


class TextReporter(Reporter):
    scope = "text"
    
    def report(self, issuemgr, fobj, directory):
        template = "{title}\n\n{senfiles}\n\n{issues}\n\n{statistics}"

        title = "{banner}\nScaning <{directory}> at {time}".format(
                banner = self.banner,
                directory = directory,
                time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        senfiles = "="*80 + "\nFound sensitive files as follows:\n\n"
        for filename in issuemgr.senfiles:
            senfiles = senfiles + "@" + filename + "\n"

        issues = "="*80 + "\nFound security issues as follows:\n\n"
        for issue in issuemgr:
            issues = issues + issue.totext()

        statistics = "="*80 + "\nStatistics information:\n"
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


