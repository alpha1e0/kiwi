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
body {{
    background-color: #DCDCDC;
}}
hr.strong {{
    border-top: 3px solid #000000;
}}
.footer {{
    font-size: 75%;
    padding: 9px 0;
    text-align: center;
    width: 100%;
}}
.content {{
    margin-left: auto;
    margin-right: auto;
    width: 80%;
    background-color: #FFFFFF;
    border-radius: 5px;
    box-shadow: 5px 5px 2px #888888;
}}
.summary {{
    padding: 15px 20px 15px 20px;
}}

.title {{
    font-size: 1.5em;
    padding-top: 5px;
    padding-bottom: 10px;
}}

.directory {{
    color: #4169E1;
}}

.time {{
    color: #4169E1;
}}

.summary-table {{
    border-collapse: collapse;
}}

.summary-table td, .summary-table th 
{{
    font-size: 1em;
    text-align: center;
    border: 2px solid #191970;
    padding: 3px 7px 2px 7px;
}}
.summary-table th {{
    font-size: 1.1em;
    padding-top: 5px;
    padding-bottom: 4px;
    background-color: #ADD8E6;
}}
.issue-block {{
    margin: 10px 10px 10px 10px;
    padding: 10px 10px 10px 10px;
    color: #696969;
    border-top: solid;
    border-top-width: 2px
}}
.issue-block b {{
    color: #000000;
}}
.issue-title {{
    font-size: 1.2em;
}}
.issue-pattern {{

}}
.issue-level-high {{
    color: #FF0000
}}
.issue-level-medium {{
    color: #F4A460
}}
.issue-level-low {{
    color: #4169E1
}}
.issue-level-info {{
    color: #66CDAA
}}
.context {{
    margin: 10px 0px 5px 0px;
    border-top: 1px solid;
    border-bottom: 1px solid;
    background-color: #F0FFFF;
}}
.context pre {{
    font-family: sans-serif;
    color: #2030a2;
    padding: 0px 5px 0px 5px
}}
</style>
</head>

<body>
<div class='content'>
<div class='summary'>
    <div class='title'>
        BugTrack. Scaning <span class='directory'>{directory}</span> at <span class='time'>{scan_time}</span> <br>
    </div>
    <hr />
    <table class='summary-table'>
        <thead>
            <tr>
                <th>严重程度</th>
                <th>High</th>
                <th>Medium</th>
                <th>Low</th>
                <th>Info</th>
                <th>编程语言</th>
                {scope_titles}
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>漏洞个数</td>
                <td>{high_num}</td>
                <td>{medium_num}</td>
                <td>{low_num}</td>
                <td>{info_num}</td>
                <td>代码行数</td>
                {scope_contents}
            </tr>
        </tbody>
    </table>
</div>

<hr class='strong' />
<div id='results'>
{issues}
</div>
</div>
<div class='footer'>
    Copyright (c) 2016 alpha1e0, See <a href='https://github.com/alpha1e0/bugtrack'>bugtrack</a>
</div>
</body>
</html>
'''

html_issue = '''
<div class='issue'>
    <div class='issue-block'>
        <div class='issue-title'><b>{issue_id}: </b> {issue_name}<br></div>
        <b>Match: </b><strong class='issue-pattern'>{pattern}</strong>&nbsp&nbsp
        <b>Severity: </b><i class='issue-level-{severity_class}'>{severity}</i>&nbsp&nbsp
        <b>Confidence: </b><i class='issue-level-{confidence_class}'>{confidence}</i></br />
        <b>File: </b><a href='{file_link}' target='_blank'>{file}</a><br />
        {reference}
        <div class='context'>
            <pre>
{code_context}
            </pre>
        </div>
    </div>
</div>
'''

html_scope_title = '''
<th>{scope}</th>
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
            confidence_class=issue['confidence'].lower(),
            issue_name=issue['name'],
            pattern=issue['pattern'],
            severity=issue['severity'],
            confidence=issue['confidence'],
            file_link=issue['file_link'],
            file=issue['filename'],
            code_context=issue['context'].rstrip(),
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

