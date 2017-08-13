#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''



class MatchContext(object):
    '''
    漏洞匹配的上下文信息类
        保存正则匹配上下文信息
        提供漏洞评价相关函数方法
    '''
    def __init__(self, filename, pattern, lineno, ctxlines):
        '''
        @params:
            filename: 漏洞匹配的相关文件文件名
            pattern:  哪个特征匹配的
            lineno:   在哪一行匹配
            ctxlines: 匹配的上下文行 [[lineno, line], ... ]
        '''
        self.filename = filename
        self.lineno = lineno
        self.pattern = pattern
        self.ctxlines = ctxlines

        for line in self.ctxlines:
            if line[0] == self.lineno:
                self._match_line = line[1]

        lines = [x[1] for x in self.ctxlines]
        self._str_ctx = "\n".join(lines)


    def get_ctx_lines(self, ctxrange):
        '''
        获取上下文信息
        @params:
            ctxrange: 整数，获取上下文的行数
        @returns:
            [(lineno, line)...]
        '''
        idx = 0
        for i in range(len(self.ctxlines)):
            if self.ctxlines[i][0] == self.lineno:
                idx = i
                break

        s = idx - ctxrange
        e = idx + ctxrange + 1

        s = s if s>=0 else 0
        e = e if e<len(self.ctxlines) else len(self.ctxlines)

        return self.ctxlines[s:e]


    def get_decoded_ctx_lines(self, ctxrange):
        '''
        获取上下文信息
            和get_ctx_lines的区别在于，对每行进行解码
        '''
        ctx_lines = self.get_ctx_lines(ctxrange)

        result = []
        for line in ctx_lines:
            try:
                decode_line = line[1].decode("utf-8")
            except UnicodeDecodeError:
                try:
                    decode_line = line[1].decode("gbk")
                except UnicodeDecodeError:
                    decode_line = repr(line[1])

            result.append((line[0], decode_line))

        return result


    @property
    def match_line(self):
        return self._match_line


    @property
    def str_ctx(self):
        return self._str_ctx


    def contains(self, keyword):
        '''
        判断漏洞特征匹配行是否包含关键字keyword
        '''
        return keyword in self._match_line


    def ctx_contains(self, keyword):
        '''
        判断漏洞特征匹配上下文是否包含关键字keyword
        '''
        return keyword in self._str_ctx




        