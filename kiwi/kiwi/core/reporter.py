#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import sys
import time
import abc
import json
import cgi

from jinja2 import Template

from common import Out
from common import conf
from issuemgr import issuemgr
from issuemgr import IssueDatabase
from filemgr import filemgr
from constant import severity_map, confidence_map, status_map
from constant import High, Medium, Low, Info



def get_reporter(filename):
    if filename.endswith(".txt"):
        return TextReporter(filename)

    if filename.endswith(".html") or filename.endswith("htm"):
        return HtmlReporter(filename)

    if filename.endswith(".db"):
        return DatabaseReporter(filename)

    if filename.endswith(".json"):
        return JsonReporter(filename)

    return TextReporter(filename)



class Reporter(object):
    scope = 'default'
    _WIDTH = 80

    def __init__(self, filename):
        self.banner = self._banner()
        self._filename = filename


    @property
    def now(self):
        '''
        字符串形式返回当前时间
        '''
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


    def _banner(self):
        '''
        return banner information
        '''
        fmt = "|{0:^" + "{0}".format(self._WIDTH-2) + "}|"

        banner = "+" + "-" * (self._WIDTH-2) + "+\n"
        banner = banner + fmt.format(
            "Kiwi. Security tool for auditing source code.") + "\n"
        banner = banner + \
            fmt.format("https://github.com/alpha1e0/kiwi") + "\n"
        banner = banner + "+" + "-" * (self._WIDTH-2) + "+\n"

        return banner


    def report(self):
        '''
        输出问题
        '''
        content = self._report()

        if content is not None:
            if not self._filename:
                print content
            else:
                with open(self._filename, 'wb') as _file:
                    if isinstance(content, unicode):
                        content = content.encode("utf-8")

                    _file.write(content)


    def _report(self):
        pass
        


class TextReporter(Reporter):
    scope = "txt"

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
            u"[{id}:{name}]\n"
            u"<Match:{pattern}> <Severity:{severity}> "
            u"<Confidence:{confidence}>\n"
            u"@{filename}\n"
            u"{context}\n")

        return template.format(
            id = issue['ID'],
            name = issue['name'],
            pattern = issue['pattern'],
            severity = severity_map[issue['severity']][0].capitalize(),
            confidence = confidence_map[issue['confidence']][0].capitalize(),
            filename = issue['filename'],
            context = self._format_issue_context(issue))
    

    def _report(self):
        template = u"{title}\n\n\n{issues}\n\n{statistics}"

        title = u"{banner}\nScaning <{directory}> at {time}".format(
                banner = self.banner,
                directory = conf.target,
                time = self.now)

        issues_content = "-"*80 + "\nFound security issues as follows:\n\n"
        for issue in issuemgr:
            issues_content = issues_content + self._format_issue(issue)

        statistics = "-"*80 + "\nStatistics information:\n"
        sinfo = issuemgr.statistics()
        for s in sinfo:
            statistics = statistics + \
                "{key}: {value}".format(key=severity_map[s][0].capitalize(), 
                    value=sinfo[s]) + "\n"

        content = template.format(
            title = title,
            issues = issues_content,
            statistics = statistics)

        return content



class ConsoleReporter(TextReporter):
    scope = "console"

    def _format_issue_context(self, issue):
        result = ""
        if not issue['context']:
            return result

        largest_lineno = issue['context'][-1][0]
        no_fmt = "{0:>" + str(len(str(largest_lineno))) + "}"

        for line in issue['context']:
            if line[0] == issue['lineno']:
                result = result + Out.Y(no_fmt.format(str(line[0])) + ": " +\
                    line[1].rstrip() + "\n")
            else:
                result = result + no_fmt.format(str(line[0])) + "- " +\
                    line[1].rstrip() + "\n"

        return result


    def _format_issue(self, issue):
        template = (
            u"[{id}:{name}]\n"
            u"<Match:{pattern}> <Severity:{severity}> "
            u"<Confidence:{confidence}>\n"
            u"@{filename}\n"
            u"{context}\n")

        return template.format(
            id = Out.R(issue['ID']),
            name = Out.G(issue['name']),
            pattern = Out.Y(issue['pattern']),
            severity = severity_map[issue['severity']][0].capitalize(),
            confidence = confidence_map[issue['confidence']][0].capitalize(),
            filename = Out.B(issue['filename']),
            context = self._format_issue_context(issue))
    

    def _report(self):
        template = u"\n{title}\n{issues}\n\n{statistics}"

        title = u"Scaning <{directory}> at {time}".format(
                directory = Out.R(conf.target),
                time = Out.R(self.now))

        issues_content = \
            Out.Y("-"*80 + "\nFound security issues as follows:\n\n")

        for issue in issuemgr:
            issues_content = issues_content + self._format_issue(issue)

        statistics = Out.Y("-"*80 + "\nStatistics information:\n")
        sinfo = issuemgr.statistics()
        for s in sinfo:
            statistics = statistics + \
                "{key}: {value}".format(key=severity_map[s][0].capitalize(), 
                    value=sinfo[s]) + "\n"

        content = template.format(
            title = title,
            issues = issues_content,
            statistics = statistics)

        return content



class HtmlReporter(Reporter):
    CONTEXT_LINE_LENGTH = 120  # HTML报告中context最大长度

    def _get_formated_issues(self):
        def _get_filelink(filename, scandir, lineno):
            opengrok_base = os.getenv("KIWI_OPENGROK_BASE")
            if not opengrok_base:
                return filename

            scandir_basename = os.path.basename(scandir)
            scandir_sp = scandir.split(os.sep)
            filename_sp = filename.split(os.sep)
            
            if len(filename_sp) <= len(scandir_sp):
                return filename
            else:
                rest_filename_sp = os.sep.join(filename_sp[len(scandir_sp):])
                return os.path.join(opengrok_base.rstrip("/"), 
                    scandir_basename, 
                    rest_filename_sp) + "#{0}".format(lineno)

        def _format_ctx_line(line):
            ret_line = cgi.escape(line)
            if len(ret_line) > self.CONTEXT_LINE_LENGTH:
                ret_line = ret_line[:self.CONTEXT_LINE_LENGTH]+"......\n"
            return ret_line


        issues = []
        i = 0
        for issue in issuemgr:
            new_issue = dict(issue)

            i += 1
            new_issue['id'] = i
            new_issue['issueid'] = issue['ID']
            new_issue['filelink'] = _get_filelink(issue['filename'],
                conf.target, issue['lineno'])

            new_issue['status_class'] = status_map[issue['status']][0]
            new_issue['status_prompt'] = status_map[issue['status']][1] 

            new_issue['severity_class'] = severity_map[issue['severity']][0]
            new_issue['severity_prompt'] = severity_map[issue['severity']][1]

            new_issue['confidence_class'] = \
                confidence_map[issue['confidence']][0]
            new_issue['confidence_prompt'] = \
                confidence_map[issue['confidence']][1]

            new_issue['context'] = [(l[0], _format_ctx_line(l[1])) \
                for l in issue['context']]

            issues.append(new_issue)

        return issues


    def _get_scan_info(self):
        scan_info = {}

        scan_info['directory'] = conf.target
        scan_info['scan_time'] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime())

        scan_info['scope_titles'] = []
        scan_info['scope_contents'] = []
        for scope,linenum in filemgr.scope_statistics.iteritems():
            scan_info['scope_titles'].append(scope)
            scan_info['scope_contents'].append(linenum)

        scan_info['severity_contents'] = \
            [v for k,v in issuemgr.statistics().iteritems()]

        return scan_info


    def _report(self):
        scan_info = self._get_scan_info()
        issues = self._get_formated_issues()

        template_file = os.path.join(conf.pkgpath, "data", 
            "html_report_template.html")

        with open(template_file) as _file:
            template = Template(_file.read().decode("utf-8"))

            return template.render(scaninfo=scan_info, issues=issues)



class JsonReporter(Reporter):
    def _report(self):
        return json.dumps(issuemgr, indent=2)



class DatabaseReporter(Reporter):
    def _report(self):
        db = IssueDatabase(self._filename)

        scope_titles = []
        scope_contents = []
        for scope,linenum in filemgr.scope_statistics.iteritems():
            scope_titles.append(scope)
            scope_contents.append(linenum)

        db.record_scan_info(conf.target, ",".join(scope_titles), 
            ",".join([str(x) for x in scope_contents]))

        for issue in issuemgr:
            db.add_issue(issue)

        return None

