#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import sys

from filemgr import filemgr
from featuremgr import featuremgr
from issuemgr import issuemgr
from reporter import TextReporter



class Analyzer(object):
    def __init__(self, directory="", exts=[], igexts=[], 
        excludes=[], gitignore=True, sctx=2, ectx=10,
        output=""):
        self.directory = directory
        self.exts = exts
        self.igexts = igexts
        self.excludes = excludes
        self.gitignore = gitignore
        self.sctx = sctx
        self.ectx = ectx
        self.output = output


    def analyze(self):
        for file in filemgr.walk(self.directory, self.exts, self.igexts, 
            self.excludes, self.gitignore):
            try:
                for feature in featuremgr[file.scope]:
                    matchctxes = file.match(feature.patterns, self.ectx)
                    for matchctx in matchctxes:
                        feature.evaluate(matchctx, self.sctx)
            except KeyError:
                continue

        reporter = TextReporter()
        reporter.report(issuemgr, sys.stdout, self.directory)

        if self.output:
            with open(self.output, "w") as _file:
                reporter.report(issuemgr, _file, self.directory)



