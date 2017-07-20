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
from filemgr import filemgr
from html_template import render_html



def get_reporter(filename):
    if filename.endswith(".txt"):
        return TextReporter()

    if filename.endswith(".html") or filename.endswith("htm"):
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

    def _format_issue_context(self, issue):
        result = ""
        if not issue['context']:
            return result

        largest_lineno = issue['context'][-1][0]
        no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"

        for line in issue['context']:
            if line[0] == issue['lineno']:
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
            context = self._format_issue_context(issue))
    

    def _report(self, fobj):
        template = "{title}\n\n\n{issues}\n\n{statistics}"

        title = "{banner}\nScaning <{directory}> at {time}".format(
                banner = self.banner,
                directory = conf.target,
                time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))

        issues_content = "-"*80 + "\nFound security issues as follows:\n\n"
        for issue in issuemgr:
            issues_content = issues_content + self._format_issue(issue)

        statistics = "-"*80 + "\nStatistics information:\n"
        sinfo = issuemgr.statistics()
        for s in sinfo:
            statistics = statistics + \
                "{key}: {value}".format(key=s, value=sinfo[s]) + "\n"

        content = template.format(
            title=title,
            issues = issues_content,
            statistics = statistics)

        fobj.write(content)
        fobj.flush()



class ConsoleReporter(TextReporter):
    scope = "console"



class HtmlReporter(Reporter):
    def _format_issue_context(self, issue):
        result = []
        if not issue['context']:
            return result

        largest_lineno = issue['context'][-1][0]
        no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"

        for line in issue['context']:
            if line[0] == issue['lineno']:
                result.append((no_fmt.format(str(line[0])), line[1], True))
            else:
                result.append((no_fmt.format(str(line[0])), line[1], False))

        return result


    def _get_file_link(self, filename):
        if not conf.opengrok_base:
            return filename

        filename_sp = os.path.split(filename)
        directory_sp = os.path.split(conf.target)

        filename_suffix_list = filename_sp[len(directory_sp)-1:]

        return conf.opengrok_base.rstrip("/") + "/" + \
            "/".join(filename_suffix_list)


    def _report(self, fobj):
        #import pdb;pdb.set_trace()
        directory = conf.target
        scan_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        statistics = [v for k,v in issuemgr.statistics().iteritems()]

        scope_titles = []
        scope_contents = []
        for scope,linenum in filemgr.scope_statistics.iteritems():
            scope_titles.append(scope)
            scope_contents.append(linenum)

        issues = []
        for issue in issuemgr:
            new_issue = dict(**issue)
            new_issue['file_link'] = self._get_file_link(issue['filename'])
            new_issue['context'] = self._format_issue_context(issue)

            issues.append(new_issue)

        html = render_html(fobj.name, directory, scan_time, statistics, 
            scope_titles, scope_contents, issues)

        fobj.write(html)
        fobj.flush()



class DatabaseReporter(Reporter):
    pass
