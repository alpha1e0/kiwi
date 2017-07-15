#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import sys

from commons import conf
from filemgr import filemgr
from featuremgr import featuremgr
from issuemgr import issuemgr
from reporter import get_reporter
from reporter import ConsoleReporter



class Analyzer(object):
    '''
    代码审计的入口
    '''
    def analyze(self):
        featuremgr.init()

        for file in filemgr.walk():
            try:
                for feature in featuremgr[file.scope]:
                    matchctxes = file.match(feature.patterns, conf.ectx)
                    for matchctx in matchctxes:
                        feature.evaluate(matchctx, conf.sctx)
            except KeyError:
                continue

        for report_name in conf.outputs:
            reporter = get_reporter(report_name)
            reporter.report(issuemgr, report_name)

        reporter = ConsoleReporter()
        reporter.report(sys.stdout)

