from taskrunner import *
import os, threading
import settings
import utils
import string

activeTasks = []
        
def addTask(command, args=[], env=os.environ):
    global activeTasks
    
    job = Job(command, command, args, env)
    name = command + " " + string.join(args, " ")
    print name
    manager = TaskRunner([Task(job)], name=name)
    job.LOGBASE = utils.escapeFilename(settings.PrefDir)
    thread = TaskRunnerThread(manager)
    thread.start()
    activeTasks.append(thread)
    