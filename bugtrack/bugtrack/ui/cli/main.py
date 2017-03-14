#!/usr/bin/env python
#-*- coding:utf-8 -*-

'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import argparse
import sys
import os

from bugtrack.core.analyzer import Analyzer



def main():
    parser = argparse.ArgumentParser(description="Bugtrack. Audit source code"
        " for security issuses")

    parser.add_argument("target", help=u"指定待扫描的目录")
    parser.add_argument("-e", "--extension", nargs="+",
        help=u"指定扫描哪些类型文件，例如-e php js则扫描.php .js文件")
    parser.add_argument("--igext", nargs="+",
        help=u"指定忽略扫描哪些类型文件，例如-e php js则扫描.php .js文件")
    parser.add_argument("--exclude", nargs="+",
        help=u"忽略扫描文件名包含关键字的文件")
    parser.add_argument("--notignoregit", action="store_true",
        help=u"不忽略gitignore指定的文件")
    parser.add_argument("-c", "--sctx", type=int, default=2,
        help=u"指定扫描结果显示的上下文行数")
    parser.add_argument("--ectx", type=int, default=10,
        help=u"指定用于评估漏洞所需的上下文信息的文件行数")
    parser.add_argument("-o", "--output", help=u"指定输出报告文件")
    
    args = parser.parse_args()

    analyzer = Analyzer()
    analyzer.directory = args.target
    analyzer.exts = args.extension
    analyzer.igexts = args.igext
    analyzer.excludes = args.exclude
    analyzer.gitignore = not args.notignoregit
    analyzer.sctx = args.sctx
    analyzer.ectx = args.ectx
    analyzer.output = args.output

    analyzer.analyze()