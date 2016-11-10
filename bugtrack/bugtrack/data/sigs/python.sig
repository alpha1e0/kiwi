%YAML 1.2
---

#===============================================================================
# Bugtrack, a sublime plugin for finding security bugs.
# Copyright (c) 2016 alpha1e0
# -----------------------------------------------------------------------------
# Issue defines for python
#===============================================================================

version: 1.0

engine: GrepEngine

scopes: 
  - python

rules:
  - PY-0001:
      severity: High
      confidence: High
      information: "Command injection"
      references: []
      patterns:
        - os.system
        - os.popen
        - commands.getoutput
        - commands.getstatusoutput

  - PY-0002:
      severity: High
      confidence: Medium
      information: "Command injection"
      references: []
      patterns:
        - subprocess.call
        - subprocess.Popen
        - subprocess.check_call
        - subprocess.check_output

  - PY-0003:
      severity: Medium
      confidence: High
      information: "File system operationg"
      references: []
      patterns:
        - os.remove
        - os.unlink
        - os.rmdir
        - os.removedirs
        - shutil.rmtree

  - PY-0004:
      severity: Low
      confidence: Low
      information: "Unsafe import"
      references: []
      patterns:
        - __import__
        - importlib.import_module
        - imp.load_module
        - imp.load_source
        - imp.load_compiled
        - imp.load_dynamic

  - PY-0005:
      severity: High
      confidence: Low
      information: "Object injection"
      references: []
      patterns:
        - pickle/cPickle
        - pickle.load
        - pickle.dump
        - yaml.load
        - yaml.dump

  - PY-0006:
      severity: High
      confidence: Low
      information: "SQL injection"
      references: []
      patterns:
        - select
        - insert
        - drop
        - delete

  - PY-0007:
      severity: High
      confidence: Medium
      information: "Evaluate a string"
      references: []
      patterns:
        - eval
        - eval_r
        - exec
        - execfile

