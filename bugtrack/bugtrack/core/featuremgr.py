#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import sys
import re
import importlib
import inspect

from exceptions import FeatureError
from commons import YamlConf
from commons import conf
from issuemgr import issuemgr
from issuemgr import Issue



class Feature(dict):
    '''
    匹配特征类
    '''
    def __init__(self, featureobj, scopes, efmgr):
        self.scopes = scopes
        self._efmgr = efmgr

        super(Feature, self).__init__(**featureobj)

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


    def _evaluate(self, *args, **kwargs):
        '''
        使用评估函数评估漏洞等级
        @returns
            字典类型，{'severity':xx, 'confidence':xx}，为空则表示不认为构成漏洞
        '''
        if 'evaluate' in self:
            return self._efmgr.run(self['evaluate'], *args, **kwargs)
        else:
            return {'severity': self.get('severity',"unknown"),
                'confidence': self.get('confidence',"unknown")}


    def evaluate(self, matchctx, ctxrange):
        '''
        评估匹配结果
            对源码文件的正则匹配结果进行评估，判断是否是漏洞，如果是则评估漏洞等级
        '''
        eresult = self._evaluate(self, matchctx)
        if eresult:
            issuemgr.add(
                ID = self['ID'],
                name = self['name'],
                scope = self.scopes,
                severity = eresult['severity'],
                confidence = eresult['confidence'],
                pattern = matchctx.pattern,
                filename = matchctx.filename,
                lineno = matchctx.lineno,
                context = matchctx.get_ctx_lines(ctxrange)
                )




class FeatureManager(object):
    def __init__(self):
        self._features = {}
        self._scopes = []

        self._efmgr = EvalfuncsManager()
        self._load_features()


    def _load_features(self):
        '''
        加载所有特征定义
        '''
        files = [os.path.join(conf.featurepath,f) \
            for f in os.listdir(conf.featurepath) \
            if f.endswith(".feature")]

        for feature_file in files:
            feature_def = YamlConf(feature_file)

            scopes = feature_def['scopes']
            features = []

            for feature in feature_def['features']:
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
    def __init__(self):
        self._evalfuncs = {}

        self._load_evalfuncs()


    def _load_evalfuncs(self):
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
    func._evaluate = True

    return func


featuremgr = FeatureManager()
efmgr = EvalfuncsManager()
