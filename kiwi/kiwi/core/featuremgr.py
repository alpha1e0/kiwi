#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import sys
import re
import importlib
import inspect

from exception import FeatureError
from common import YamlConf
from common import conf
from issuemgr import issuemgr
from issuemgr import Issue
from constant import High, Medium, Low, Info



class Feature(dict):
    '''
    漏洞特征类，管理正则特征、调用漏洞评价函数进行漏洞确认
    '''

    High = High
    Medium = Medium
    Low = Low
    Info = Info

    def __init__(self, featureobj, scopes, efmgr):
        self.scopes = scopes
        self._efmgr = efmgr

        super(Feature, self).__init__(**featureobj)

        if 'severity' not in self:
            self['severity'] = Info
        else:
            try:
                self['severity'] = getattr(self, self['severity'])
            except KeyError:
                self['severity'] = Info

        if 'confidence' not in self:
            self['confidence'] = Low
        else:
            try:
                self['confidence'] = getattr(self, self['confidence'])
            except KeyError:
                self['confidence'] = Low

        self._init_patterns()


    def _init_patterns(self):
        repatterns = []

        for pattern in self['patterns']:
            rp = re.compile(pattern)

            repatterns.append(rp)

        self['patterns'] = repatterns


    @property
    def patterns(self):
        return self['patterns']


    @property
    def level(self):
        return {'severity': self.get('severity',"unknown"),
            'confidence': self.get('confidence',"unknown")}


    def _evaluate(self, matchctx):
        '''
        使用评估函数评估漏洞等级
        @returns
            字典类型，('severity', 'confidence')，为空则表示不认为构成漏洞
        '''
        if 'evaluate' in self:
            return self._efmgr.run(self['evaluate'], self, matchctx)
        else:
            return (self.get('severity', Low),
                self.get('confidence', Low))


    def evaluate(self, matchctx, ctxrange):
        '''
        评估匹配结果
            对源码文件的正则匹配结果进行评估，判断是否是漏洞，如果是则评估漏洞等级
        @params:
            matchctx: 特征匹配的上下文信息
            ctxrange: 漏洞中保存的上下文信息行数
        '''
        evaluate_result = self._evaluate(matchctx)

        if evaluate_result:
            issuemgr.add(
                ID = self['ID'],
                name = self['name'],
                scope = self.scopes,
                severity = evaluate_result[0],
                confidence = evaluate_result[1],
                pattern = matchctx.pattern,
                filename = matchctx.filename,
                lineno = matchctx.lineno,
                context = matchctx.get_decoded_ctx_lines(ctxrange)
                )




class FeatureManager(object):
    '''
    漏洞特征管理器
    '''
    def __init__(self):
        # _scopes 列表，记录特征库中支持的所有 sope
        self._scopes = []

        # _features 字典，{scope, featues}，记录所有scope和其相关的features
        self._features = {}


    def init(self):
        '''
        初始化 漏洞特征管理器，加载所有指定的漏洞特征
        '''
        # _dfmgr，漏洞评价函数管理器，用于加载、调用评价函数
        self._efmgr = EvalfuncsManager()

        files = [os.path.join(conf.featurepath,f) \
            for f in os.listdir(conf.featurepath) \
            if f.endswith(".feature")]

        for feature_file in files:
            feature_def = YamlConf(feature_file)

            scopes = feature_def['scopes']
            features = []

            for feature in feature_def['features']:
                if conf.feature_ids:
                    if feature['ID'] not in conf.feature_ids:
                        continue
                features.append(Feature(feature, scopes, self._efmgr))

            for scope in scopes:
                if scope in self._features:
                    self._features[scope] += features
                else:
                    self._features[scope] = features
                    self._scopes.append(scope)


    @property
    def scopes(self):
        return self._scopes


    def __getattr__(self, scope):
        if scope in self._scopes:
            return self._features[scope]
        else:
            raise AttributeError("scope {} not found".format(scope))


    def __getitem__(self, scope):
        if scope in self._scopes:
            return self._features[scope]
        else:
            raise KeyError("scope {} not found".format(scope))



class EvalfuncsManager(object):
    '''
    漏洞评价函数管理器
    '''
    def __init__(self):
        # _evalfuncs 存储所有漏洞评价函数
        self._evalfuncs = {}

        self._load_evalfuncs()


    def _load_evalfuncs(self):
        '''
        加载漏洞评价函数
        '''
        files = [f[:-3] for f in os.listdir(conf.evalpath) if f.endswith(".py")]

        if conf.evalpath not in sys.path:
            sys.path.append(conf.evalpath)

        for evalfile in files:
            try:
                module = importlib.import_module(evalfile)
            except ImportError:
                raise FeatureError("import evaluate file '{}' failed"\
                    .format(evalfile))

            for member in dir(module):
                func = getattr(module, member)
                if inspect.isfunction(func) and hasattr(func, "_evaluate"):
                    self._evalfuncs[member] = func


    def run(self, funcname, *args, **kwargs):
        try:
            func = self._evalfuncs[funcname]
        except KeyError:
            raise FeatureError("can not find evaluate function '{}".format(
                funcname))

        return func(*args, **kwargs)



def evaluate(func):
    '''
    漏洞评估函数修饰器
        使用方法示例：
        @evaluate
        def py_cmd_inject_eval(feature, matchctx):
            return (severity, confidence)
    '''
    func._evaluate = True

    return func


featuremgr = FeatureManager()
