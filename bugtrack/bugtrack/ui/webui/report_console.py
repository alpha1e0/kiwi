#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import argparse

import eventlet
from eventlet import wsgi

from bugtrack.core.common import Out
from application import application



def main():
    out = Out()
    out.init(u"BugTrack 报告查看器")

    parser = argparse.ArgumentParser(description="Bugtrack. Audit source code"
        " for security issuses")

    parser.add_argument("-p", "--port", type=int, 
        help=u"指定监听端口，默认为5000")
    parser.add_argument("--ip", help=u"指定监听IP")
    parser.add_argument("-d", "--report_path", help=u"指定扫描报告目录")
    
    args = parser.parse_args()

    port = args.port or 5000
    ip = args.ip or '0.0.0.0'
    report_path = args.report_path or os.getenv("BUGTRACK_REPORT_PATH")

    if not report_path:
        out.error(u"未指定报告目录，请使用-d/--report_path参数或者"
            u"BUGTRACK_REPORT_PATH环境变量指定报告目录")
        exit(1)

    application.report_path = os.path.realpath(report_path)

    wsgi.server(eventlet.listen((ip, port)), application)



if __name__ == '__main__':
    main()

