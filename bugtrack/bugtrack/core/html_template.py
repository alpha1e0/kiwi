#!/usr/bin/env python
#-*- coding:utf-8 -*-


'''
Bugtrack, Security tool for auditing source code
--------------------------------------------------------------------------------
Copyright (c) 2016 alpha1e0
'''


html = '''
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta name="author" content="alpha1e0" />
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>
    {report_name}
</title>

<style>
html * {{
    font-family: "Arial", sans-serif;
}}
pre {{
    font-family: "Monaco", monospace;
}}
.bordered-box {{
    border: 1px solid black;
    padding-top:.5em;
    padding-bottom:.5em;
    padding-left:1em;
}}
.metrics-box {{
    font-size: 1.1em;
    line-height: 130%;
}}
.metrics-title {{
    font-size: 1.5em;
    font-weight: 500;
    margin-bottom: .25em;
}}
.issue-description {{
    font-size: 1.3em;
    font-weight: 500;
}}
.candidate-issues {{
    margin-left: 2em;
    border-left: solid 1px; LightGray;
    padding-left: 5%;
    margin-top: .2em;
    margin-bottom: .2em;
}}
.issue-block {{
    border: 1px solid LightGray;
    padding-left: .5em;
    padding-top: .5em;
    padding-bottom: .5em;
    margin-bottom: .5em;
}}
.issue-sev-high {{
    background-color: Pink;
}}
.issue-sev-medium {{
    background-color: NavajoWhite;
}}
.issue-sev-low {{
    background-color: LightCyan;
}}
#footer {{
    font-size: 75%;
    padding: 9px 0;
    text-align: center;
    width: 100%;
}}
</style>
</head>

<body>
<div id='summary'>
    <div class='metrics-box bordered-box'>
        <div class='metrics-title'>
            Scaning {directory} at {scan_time} <br>
        </div>
        <table id='summary-table' border="1">
            <tr>
            <th>严重程度</th>
            <th>High</th>
            <th>Medium</th>
            <th>Low</th>
            <th>Info</th>
            <th>编程语言</th>
            {scope_titles}
            </tr>
            <tr>
            <th>漏洞个数</th>
            <td>{high_num}</td>
            <td>{medium_num}</td>
            <td>{low_num}</td>
            <td>{info_num}</td>
            <th>代码行数</th>
            {scope_contents}
            </tr>
        </table>
    </div>
</div>

<hr />
<div id='results'>
{issues}
</div>
<div id='footer'>
    Copyright (c) 2016 alpha1e0, See <a href='https://github.com/alpha1e0/bugtrack'>bugtrack</a>
</div>
</body>
</html>
'''

html_issue = '''
<div id='{issue_id}'>
    <div class='issue-block issue-sev-{severity_class}'>
        <b>{issue_id}: </b> {issue_name}<br>
        <b>Match: </b>{pattern}&nbsp&nbsp
        <b>Severity: </b>{severity}&nbsp&nbsp
        <b>Confidence: </b>{confidence}</br />
        <b>File: </b><a href='{file_link}' target='_blank'>{file}</a><br />
        {reference}
        <div id='code'>
            <pre>
{code_context}
            </pre>
        </div>
    </div>
</div>
'''

html_scope_title = '''
<td>{scope}</td>
'''

html_scope_content = '''
<td>{codelines}</td>
'''

html_reference = '''
<b>References: </b><a href='{reference}' target='_blank'>{reference}</a><br />
'''


def render_html(report_name, directory, scan_time, statistics, scope_titles, 
    scope_contents, issues):
    '''
    render html模板
    @params:
        issues: 列表，列表的每项用来填充html_issue
        scope_titles: 列表，列表的每项用来填充html_scope_title
        scope_contents: 列表，列表的每项用来填充html_scope_content
    '''
    scope_titles_content = "\n".join(
        [html_scope_title.format(scope=st) for st in scope_titles])

    scope_contents_content = "\n".join(
        [html_scope_content.format(codelines=n) for n in scope_contents])

    issues_list = []
    for issue in issues:
        reference = "" if not issue.get('reference', None) else \
            html_reference.format(reference, issue.get('reference'))

        issue_content = html_issue.format(
            issue_id=issue['ID'],
            severity_class=issue['severity'].lower(),
            issue_name=issue['name'],
            pattern=issue['pattern'],
            severity=issue['severity'],
            confidence=issue['confidence'],
            file_link=issue['file_link'],
            file=issue['filename'],
            code_context=issue['context'],
            reference=reference
            )

        issues_list.append(issue_content)

    issues_content = "\n".join(issues_list)

    return html.format(
        report_name=report_name,
        directory=directory,
        scan_time=scan_time,
        high_num=statistics[0],
        medium_num=statistics[1],
        low_num=statistics[2],
        info_num=statistics[3],
        scope_titles=scope_titles_content,
        scope_contents=scope_contents_content,
        issues=issues_content
        )

