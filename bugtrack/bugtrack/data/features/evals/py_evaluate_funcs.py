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
    if "shell=True" in matchctx.matchline:
        return feature.level
    else:
        return False