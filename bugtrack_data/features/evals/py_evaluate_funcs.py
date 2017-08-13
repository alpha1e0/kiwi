#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


from bugtrack.core.featuremgr import evaluate



@evaluate
def py_cmd_inject_0002(feature, matchctx):
    if matchctx.contains("shell=True"):
        return (feature['severity'], feature['confidence'])
    else:
        return None