#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


from kiwi.core.featuremgr import evaluate


@evaluate
def php_file_inclusion_001_evaluate(feature, matchctx):
    if matchctx.contains("$"):
        return (feature['severity'], feature['confidence'])
    else:
        return None