from builtins import object
import os, sys, string

# -------------------------------------------------------------------------
# ExtProcess helper class
# Code copyright 2004-2005 Vaclav Slavik
# Code added with permission from original author
# -------------------------------------------------------------------------

if sys.platform == 'win32':
    import win32api, win32con, win32process
    
    class ExtProcess(object):
        def __init__(self, cmd):
            cmd2 = ' '.join(['"%s"' % x for x in cmd])
            procArgs = (None,  # appName
                        cmd2,  # commandLine
                        None,  # processAttributes
                        None,  # threadAttributes
                        1,     # bInheritHandles
                        win32con.CREATE_NO_WINDOW,     # dwCreationFlags
                        None,  # newEnvironment
                        None,  # ProjectDirectory
                        win32process.STARTUPINFO()) # startupinfo
            procHandles = win32process.CreateProcess(*procArgs)
            self.handle, self.thread, self.pid, self.tid = procHandles
        
        def isAlive(self):
            try:
                st = win32process.GetExitCodeProcess(self.handle)
                return st == win32con.STILL_ACTIVE
            except win32api.error:
                return False
        
        def kill(self):
            win32api.TerminateProcess(self.handle, 0)
    
else: # Unix/Mac
    
    class ExtProcess(object):
        def __init__(self, cmd):
            self.pid = os.spawnv(os.P_NOWAIT, cmd[0], cmd)
        
        def kill(self):
            os.waitpid(self.pid, 0)
        
        def isAlive(self):
            try:
                pid, exitstatus = os.waitpid(self.pid, os.WNOHANG)
                return pid == 0
            except os.error:
                return False
