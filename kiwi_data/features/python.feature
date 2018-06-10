%YAML 1.2
---

#===============================================================================
# Kiwi, Security tool for auditing source code
# Copyright (c) 2016 alpha1e0
# -----------------------------------------------------------------------------
# Issue defines for python
#===============================================================================

version: 1.0

scopes: 
  - python


features:
- ID: PY_CMD_INJ_001
  name: "Use 'os/commands' module to execute command in shells"
  references: []
  severity: High
  confidence: High
  patterns:
    - os.system
    - os.popen
    - os.popen2
    - os.popen3
    - os.popen4
    - popen2.popen2
    - popen2.popen3
    - popen2.popen4
    - popen2.Popen3
    - popen2.Popen4
    - commands.getoutput
    - commands.getstatusoutput


- ID: PY_CMD_INJ_002
  name: "Use 'subprocess' module with shell=True to execute command in shells"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - subprocess.call
    - subprocess.Popen
    - subprocess.check_call
    - subprocess.check_output
    - utils.execute
    - utils.execute_with_timeout
  evaluate: py_cmd_inject_0002_evaluate


- ID: PY_CMD_EXE_001
  name: "File system operation"
  severity: Medium
  confidence: High
  
  references: []
  patterns:
    - os.remove
    - os.unlink
    - os.rmdir
    - os.removedirs
    - shutil.rmtree


- ID: PY_OBJ_INJ_001
  name: "Pickle operation"
  severity: High
  confidence: Low
  references: []
  patterns:
    - pickle/cPickle
    - pickle.load
    - pickle.dump
    - yaml.load
    - yaml.dump


- ID: PY_SQL_INJ_001
  name: "SQL injection"
  severity: High
  confidence: Low
  references: []
  patterns:
    - \["']select.+from
    - \["']insert.+into
    - \["']update.+set
    - \["']drop
    - \["']delete.+from


- ID: PY_EXEC_FUNC_0001
  name: "Evaluate a string"
  severity: High
  confidence: Medium
  references: []
  patterns:
    - \beval\b
    - \beval_r\b
    - \bexec\b
    - \bexecfile\b


- ID: PY_RUNING_IMPORT_0001
  name: "Unsafe import"
  severity: Low
  confidence: Low
  references: []
  patterns:
    - __import__
    - importlib.import_module
    - imp.load_module
    - imp.load_source
    - imp.load_compiled
    - imp.load_dynamic







