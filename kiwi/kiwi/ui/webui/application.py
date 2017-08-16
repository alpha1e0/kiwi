#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Kiwi, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


import os
import json

from flask import Flask
from flask import request
from flask import render_template
from flask import redirect
from flask import url_for

from kiwi.core.issuemgr import IssueDatabase
from kiwi.core.constant import status_map, severity_map, confidence_map
from kiwi.core.constant import High, Medium, Low, Info
from kiwi.core.constant import New, Old, Falsep



application = Flask(__name__)

application.report_path = None



def get_reports(report_path, current_report=None):
    reports = []

    for name in os.listdir(report_path):
        if name.endswith(".db"):
            reports.append(name[:-3])

    reports.sort()

    return reports



def get_formated_issues(origin_issues, scan_info):
    def _get_filelink(filename, scandir):
            opengrok_base = os.getenv("KIWI_OPENGROK_BASE")
            if not opengrok_base:
                return filename

            scandir_sp = os.path.split(scandir)
            filename_sp = os.path.split(filename)
            
            if len(filename_sp) <= len(scandir_sp):
                return filename
            else:
                rest_filename_sp = filename_sp[len(scandir_sp):]
                return os.path.join(opengrok_base, rest_filename_sp)


    issues = []
    for issue in origin_issues:
        new_issue = dict(issue)

        new_issue['id'] = issue['id']
        new_issue['issueid'] = issue['issueid']
        new_issue['filelink'] = _get_filelink(issue['filename'], 
            scan_info['directory'])

        new_issue['context'] = json.loads(issue['context'])

        new_issue['status_class'] = status_map[issue['status']][0]
        new_issue['status_prompt'] = status_map[issue['status']][1] 

        new_issue['severity_class'] = severity_map[issue['severity']][0]
        new_issue['severity_prompt'] = severity_map[issue['severity']][1]   

        new_issue['confidence_class'] = confidence_map[issue['confidence']][0]
        new_issue['confidence_prompt'] = confidence_map[issue['confidence']][1]

        issues.append(new_issue)

    return issues


def get_scan_info(origin_scan_info, reports, current_report, severity_info,
    status_info):
    scan_info = {}
    scan_info['reports'] = reports
    scan_info['selected_report'] = current_report

    scan_info['directory'] = origin_scan_info['directory']
    scan_info['scan_time'] = origin_scan_info['scan_time']
    scan_info['scope_titles'] = origin_scan_info['scope_titles'].split(",")
    scan_info['scope_contents'] = origin_scan_info['scope_contents'].split(",")

    scan_info['severity_contents'] = [v for k,v in severity_info.iteritems()]
    scan_info['status_contents'] = [v for k,v in status_info.iteritems()]

    return scan_info



@application.route('/')
def index():
    return redirect(url_for('view_report'))


@application.route('/view', methods=['GET'])
def view_report():
    try:
        current_report = request.args['name']
    except KeyError:
        current_report = None

    reports = get_reports(application.report_path)
    current_report = current_report or reports[0]

    report_file = os.path.join(application.report_path, current_report) + ".db"
    rdb = IssueDatabase(report_file)

    origin_scan_info = rdb.get_scan_info()[0]
    severity_info, status_info = rdb.statistics()

    scan_info = get_scan_info(origin_scan_info, reports, current_report, 
        severity_info, status_info)

    new_issues, old_issues, falsep_issues = rdb.get_classfied_issues()
    issues = get_formated_issues(new_issues+old_issues+falsep_issues, scan_info)

    return render_template('page.html', 
        scaninfo=scan_info,
        issues=issues)


@application.route("/modify", methods=['POST'])
def modify():
    try:
        report_name = request.form['name']
        issue_id = request.form['id']
        falsep = request.form['falsep']
        comment = request.form['comment']
    except KeyError:
        return "Error: missing parameter"

    report_file = os.path.join(application.report_path, report_name) + ".db"
    rdb = IssueDatabase(report_file)

    if falsep:
        status = Falsep
    else:
        status = None

    rdb.modify(issue_id, status, comment)

    return redirect(url_for('view_report', name=report_name))




