###########################################################################
# Bugtrack, a sublime plugin for finding security bugs.
# Copyright (c) 2016 alpha1e0
# ======================================================================
# signature file for python
###########################################################################


- os.system
- os.popen
- subprocess.call
- subprocess.Popen
- subprocess.check_call
- subprocess.check_output
- commands.getoutput
- commands.getstatusoutput
- os.remove
- os.unlink
- os.rmdir
- os.removedirs
- shutil.rmtree
- write/writelines
- __import__
- importlib.import_module
- imp.load_module
- imp.load_source
- imp.load_compiled
- imp.load_dynamic
- pickle/cPickle
- pickle.load
- pickle.dump
- yaml.load
- yaml.dump
- select
- insert
- drop
- delete
- eval
- eval_r
- exec
- execfile
- compile