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
    '''
    文件类，用于正则匹配
    '''
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
    def length(self):
        return len(self._formated_lines)


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
        '''
        获取匹配上下文信息
        '''
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
            patterns: 待匹配的正则表达式的列表
            ctxrange: 记录多少行上下文信息
        @return:
            [MatchContext, ...]
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
    '''
    文件管理类
    '''
    _METAINFOLEN = 50

    def __init__(self):
        # 文件类型映射信息，结构:
        #     {'extensions': 
        #         [{'pattern':xx, 'scope':xx}, ...]
        #      'metainfos':
        #         [{'pattern':xx, 'scope':xx}, ...]
        #     }
        #
        self._map_conf = {}
        # 敏感文件定义信息，结构：
        #     {'patterns':[pattern, ...]}
        self._senfile_conf = {}

        # 保存文件统计信息
        self._scope_statistics = {}

        self._gitignores = []


    def init(self):
        self._load_map_conf()
        self._load_senfiles_conf()


    @property
    def scope_statistics(self):
        return self._scope_statistics


    def _load_map_conf(self):
        '''
        加载文件类型映射信息
        '''
        config = YamlConf(conf.mapfile)

        self._map_conf['extensions'] = []
        self._map_conf['metainfos'] = []

        for ext in config['extensions']:
            self._map_conf['extensions'].append({
                'pattern': re.compile(ext['pattern']),
                'scope': ext['scope']
                })

        for meta in config['metainfos']:
            self._map_conf['metainfos'].append({
                'pattern': re.compile(meta['pattern']),
                'scope': meta['scope']
                })


    def _load_senfiles_conf(self):
        '''
        加载敏感可以文件配置
        '''
        config = YamlConf(conf.senfiles)

        self._senfile_conf['patterns'] = []
        for pattern in config['patterns']:
            self._senfile_conf['patterns'].append(re.compile(pattern))


    def _add_sensitive_file(self, filename, scope):
        '''
        通过文件名判断是否是可疑敏感文件
        '''
        for pattern in self._senfile_conf['patterns']:
            if pattern.search(filename):
                issuemgr.add_senfile(filename, scope, pattern)
                return



    def is_file_skip(self, filename):
        '''
        通过参数配置根据文件名过滤文件
        '''
        filename_sp = os.path.split(filename)
        for vs in ['.git', 'CVS', '.svn']:
            if vs in filename_sp:
                return True

        if conf.excludes:
            for kw in conf.excludes:
                if kw in filename:
                    return True

        if conf.igexts:
            for ext in conf.igexts:
                if filename.endswith(ext):
                    return True

        if conf.extensions:
            is_ext_match = False
            for ext in conf.extensions:
                if filename.endswith(ext):
                    is_ext_match = True
                    break
            
            if not is_ext_match:
                return True


    def walk(self):
        target_dir = os.path.realpath(conf.target)
        if not os.path.exists(target_dir):
            raise FileError("cannot find directory {}".format(target_dir))

        for path, dirs, files in os.walk(target_dir):
            for f in files:
                filename = os.path.join(path, f)
                if self.is_file_skip(filename):
                    continue

                scope = self._classify(filename)
                if not scope:
                    continue

                self._add_sensitive_file(filename, scope)

                file = File(filename, scope)
                if scope in self._scope_statistics:
                    self._scope_statistics[scope] += file.length
                else:
                    self._scope_statistics[scope] = file.length

                yield file


    def _classify(self, filename):
        '''
        判断文件类型，将文件类型映射到相应的scope
        '''
        for ext in self._map_conf['extensions']:
            m = ext['pattern'].search(filename)
            if m:
                return ext['scope']

        for meta in self._map_conf['metainfos']:
            with open(filename) as _file:
                content = _file.read(self._METAINFOLEN)
                m = meta['pattern'].search(content)
                if m:
                    return meta['scope']

        return None



filemgr = FileManager()