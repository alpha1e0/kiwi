#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import re

from commons import YamlConf
from commons import conf
from context import MatchContext
from exceptions import FileError
from issuemgr import issuemgr



class File(object):
    def __init__(self, filename, scope, maxlen=0):
        self._filename = filename
        self._scope = scope

        if not os.path.exists(self._filename):
            raise FileError("cannot find file '{0}'".format(self._filename))

        try:
            self._file = open(self._filename)
        except IOError:
            raise FileError("read file '{0}' error".format(self._filename))

        if maxlen == 0:
            self._content = self._file.read()
        elif maxlen > 0:
            self._content = self._file.read(maxlen)
        else:
            self._content = ""

        # format [line, (start,end)]
        self._formated_lines = self._get_formated_lines()



    @property
    def filename(self):
        return self._filename

    @property
    def scope(self):
        return self._scope


    def is_text_file(self):
        return True


    def _get_formated_lines(self):
        '''
        文件内容格式化
            将文本格式化为[line,(start,end)]列表，start/end表示每一行的开始、结束索引
        '''
        result = []
        sp = self._content.split("\n")
        start = end = 0

        for l in sp:
            start = end
            end = end + len(l) + 1
            result.append([l+"\n",(start, end)])

        return result


    def get_context_lines(self, lineno, ctxrange):
        result = []

        data_lines_len = len(self._formated_lines)
        if lineno>data_lines_len or lineno<0:
            return ""

        sidx = lineno - (ctxrange+1)
        if sidx<0: sidx=0
        eidx = lineno + ctxrange
        eidx = eidx if eidx<data_lines_len else data_lines_len

        for i in range(sidx+1, eidx+1):
            result.append((i,self._formated_lines[i-1][0]))

        return result



    def match(self, patterns, ctxrange):
        '''
        @params:
            patterns: 记录待匹配的正则表达式的列表
            ctxrange: 记录多少行上下文信息
        @return:
            [filename, pattern, lineno, context]
                context [[lineno, line],...]
        '''
        result = []
        for pattern in patterns:
            for match in pattern.finditer(self._content):
                for index, line in enumerate(self._formated_lines):
                    if match.start()>=line[1][0] and match.start()<line[1][1]:
                        ctxlines = self.get_context_lines(index+1, ctxrange)
                        matchctx = MatchContext(self._filename, pattern.pattern, 
                            index+1, ctxlines)

                        result.append(matchctx)
                        break

        return result



class FileManager(object):
    _METAINFOLEN = 50

    def __init__(self):
        self._mapconf = {}
        self._senfileconf = {}

        self._load_map_conf()
        self._load_senfiles_conf()

        self._gitignores = []


    def _load_map_conf(self):
        config = YamlConf(conf.mapfile)

        self._mapconf['extensions'] = []
        self._mapconf['metainfos'] = []

        for ext in config['extensions']:
            self._mapconf['extensions'].append({
                'pattern': re.compile(ext['pattern']),
                'scope': ext['scope']
                })

        for meta in config['metainfos']:
            self._mapconf['metainfos'].append({
                'pattern': re.compile(meta['pattern']),
                'scope': meta['scope']
                })


    def _load_senfiles_conf(self):
        '''
        load the configure of sensitive files
        '''
        config = YamlConf(conf.senfiles)

        self._senfileconf['patterns'] = []
        for pattern in config['patterns']:
            self._senfileconf['patterns'].append(re.compile(pattern))


    def _is_sensitive_file(self, filename):
        for pattern in self._senfileconf['patterns']:
            if pattern.search(filename):
                return True

        return False


    def _gitignore(self, filename, directory):
        if ".git" in filename:
            return True

        if self._gitignores:
            for i in self._gitignores:
                if i in filename:
                    return True

        if os.path.exists(os.path.join(directory, ".gitignore")):
            with open(os.path.join(directory, ".gitignore")) as _file:
                self._gitignores = _file.read().splitlines()

                for i in self._gitignores:
                    if i in filename:
                        return True
        else:
            return False


    def isskip(self, filename, directory, exts, igexts, excludes, gitignore):
        if gitignore:
            if self._gitignore(filename, directory):
                return True

        if excludes:
            for kw in excludes:
                if kw in filename:
                    return True

        if igexts:
            for ext in igexts:
                if filename.endswith(ext):
                    return True

        if exts:
            is_ext_match = False
            for ext in exts:
                if filename.endswith(ext):
                    is_ext_match = True
                    break
            
            if not is_ext_match:
                return True


    def walk(self, directory, exts, igexts, excludes, gitignore):
        self._directory = os.path.realpath(directory)
        if not os.path.exists(self._directory):
            raise FileError("cannot find directory {}".format(self._directory))

        for path, dirs, files in os.walk(self._directory):
            for f in files:
                filename = os.path.join(path, f)
                if self.isskip(filename, directory, exts, igexts, excludes, 
                    gitignore):
                    continue

                if self._is_sensitive_file(filename):
                    issuemgr.add_senfile(filename)

                scope = self._classify(filename)
                if not scope:
                    continue

                yield File(filename, scope)


    def _classify(self, filename):
        '''
        判断文件类型，将文件类型映射到相应的scope
        '''
        for ext in self._mapconf['extensions']:
            m = ext['pattern'].search(filename)
            if m:
                return ext['scope']

        for meta in self._mapconf['metainfos']:
            with open(filename) as _file:
                content = _file.read(self._METAINFOLEN)
                m = meta['pattern'].search(content)
                if m:
                    return meta['scope']

        return None



filemgr = FileManager()