from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
hasTaskRunner=False

try:
    from externals.taskrunner import *
    hasTaskRunner=True
except:
    pass
    
import os, threading
import settings
import utils
import string

activeTasks = []
        
def addTask(command, args=[], env=os.environ):
    global activeTasks
    if hasTaskRunner:
    
        job = Job(os.path.basename(command), command, args, env)
        name = command + " " + string.join(args, " ")
        print(name)
        manager = TaskRunner([Task(job)], name=name)
        job.LOGBASE = utils.escapeFilename(settings.PrefDir)
        thread = TaskRunnerThread(manager)
        thread.start()
        activeTasks.append(thread)
    
