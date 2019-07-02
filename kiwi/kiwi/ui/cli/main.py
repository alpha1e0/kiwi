#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import sys
import argparse

from kiwi.core.common import conf
from kiwi.core.common import Out
from kiwi.core.analyzer import Analyzer
from kiwi.core.reporter import get_reporter
from kiwi.core.reporter import ConsoleReporter



class TargetParamParser(argparse.Action):
    def __call__(self, parser, namespace, values, option_string=None):
        setattr(namespace, self.dest, os.path.abspath(values))


class IDParamParser(argparse.Action):
    '''
    fileop模块file类型参数处理器
    @remarks:
        filePath@fileType参数 处理为 (filePath, fileType)
        filePath 处理为 (filePath, None)
    '''
    def __call__(self, parser, namespace, values, option_string=None):
        new_values = []

        for value in values:
            if value.startswith("@"):
                file_name = value[1:]
                try:
                    with open(file_name) as _file:
                        for line in _file:
                            line = line.strip()

                            if line.startswith("#"):
                                continue
                            if not line:
                                continue

                            new_values.append(line)
                except IOError:
                    Out.error("can not open file {0}".format(file_name))
            else:
                new_values.append(value)

        setattr(namespace, self.dest, new_values)



def main():
    out = Out()
    out.init(u"Kiwi 代码安全扫描")

    parser = argparse.ArgumentParser(description=u"Kiwi. 代码安全审计工具")

    parser.add_argument("-t", "--target", required=True, 
        action=TargetParamParser, help=u"指定待扫描的目录")
    parser.add_argument("-f", "--feature_dir", help=u"指定漏洞特征定义目录")
    parser.add_argument("-i", "--feature_ids", nargs="+", action=IDParamParser,
        help=u"指定加载哪些漏洞特征")
    parser.add_argument("-e", "--extensions", nargs="+",
        help=u"指定扫描哪些类型文件，例如-e php js则扫描.php .js文件")
    parser.add_argument("--igexts", nargs="+",
        help=u"指定忽略扫描哪些类型文件，例如--igexts php js则忽略扫描.php .js文件")
    parser.add_argument("--excludes", nargs="+",
        help=u"忽略扫描文件路径包含关键字的文件")
    parser.add_argument("-c", "--sctx", type=int, default=2,
        help=u"指定扫描结果显示的上下文行数")
    parser.add_argument("--ectx", type=int, default=10,
        help=u"指定用于评估漏洞所需的上下文信息的文件行数")
    parser.add_argument("-o", "--outputs", nargs="+",
        help=u"指定输出报告文件，支持.txt/.html/.json/.db")
    parser.add_argument("-v", "--verbose", action="store_true",
        help=u"详细模式，输出扫描过程信息")
    
    args = parser.parse_args()

    conf.init_args(args)

    out.info(u"kiwi 扫描 {0} ...".format(conf.target, ))
    Analyzer().analyze()

    if conf.outputs:
        out.info(u"kiwi 生成报告 {0}".format(",".join(conf.outputs)))
        for report_name in conf.outputs:
            reporter = get_reporter(report_name)
            reporter.report()
    else:
        reporter = ConsoleReporter(None)
        reporter.report()

    out.close()

