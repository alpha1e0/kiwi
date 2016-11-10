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
  - python  # this value is related to filemaping

# the rule will be passed to the engine as a parameter, so the format depends on the engine
# the rule should aways include 'severity' 'confidence' 'information' 
rules:
  - PY-0001:
      severity: High    # reference value, finally the engine will determine the final value
      confidence: High  # reference value, finally the engine will determine the final value
      information: "xxxxx"  # 
      references: ["http://xx.org"]
      patterns:
        - os.system
        - os.popen
        - commands.getoutput
        - commands.getstatusoutput
      




