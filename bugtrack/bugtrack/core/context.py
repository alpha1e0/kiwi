#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


class MatchContext(object):
    def __init__(self, filename, pattern, lineno, ctxlines):
        self.filename = filename
        self.lineno = lineno
        self.pattern = pattern
        self.ctxlines = ctxlines


    def get_ctx_lines(self, ctxrange):
        idx = 0
        for i in range(len(self.ctxlines)):
            if self.ctxlines[i][0] == self.lineno:
                idx = i
                break

        s = idx - ctxrange
        e = idx + ctxrange + 1

        s = s if s>=0 else 0
        e = e if e<len(self.ctxlines) else len(self.ctxlines)

        return self.ctxlines[s:e]


    @property
    def matchline(self):
        for line in self.ctxlines:
            if line[0] == self.lineno:
                return line[1]

        return ""
        