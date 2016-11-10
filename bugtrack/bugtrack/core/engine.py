#-*- coding:utf-8 -*-


'''
Bugtrack, a sublime plugin for finding security bugs.
-----------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import re
import codecs

from libs.commons import FileError
from libs.commons import YamlConf
from libs.thirdparty import grin



class Engine(object):
    def __init__(self):
        pass


    def analyse(self, fileName, pattern):
        '''
        @returns
            return the 'match-entry' list, the format of 'match entry' is:
                [line-number, match-string, match-index-list]
                    line-number: integer number indicate the line number matchs
                    match-string: match string
                    index-list: a list of matchs index, likes [(3,6),(8,11)]
        '''
        grebob = grin.GrepText(re.compile(pattern))

        try:
            with open(fileName, encoding='utf-8') as _file:
                searchResult = grebob.do_grep(_file)
        except UnicodeDecodeError:
            try:
                with open(fileName, encoding='gbk') as _file:
                    searchResult = grebob.do_grep(_file)
            except UnicodeDecodeError:
                #raise FileError("read/decode file {0} error".format(fileName))
                return []
            except LookupError:
                return []
        
        return [((x[0]+1), x[2], x[3]) for x in searchResult]
        


class GrepEngine(Engine):
    def __init__(self):
        pass


    def analyse(self, target, signature):






