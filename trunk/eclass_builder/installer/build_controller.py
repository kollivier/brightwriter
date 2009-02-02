import sys, os, string, time, shutil
#import ReleaseForge

from taskrunner import Job, Task, TaskRunner, TaskRunnerThread, Config
import glob

# read in the build settings...

CFGFILE = "./build-environ.cfg"
config = Config()
config.read(CFGFILE)

package_exts = [".dmg", ".exe", ".rpm", ".tar.gz", ".tar.bz", ".tgz", ".zip"]

def getDistribFiles():
    # get a list of files that should be uploaded by checking the deliver directory
    filelist = []
    for ext in package_exts:
        filelist += glob.glob("deliver/*"+ext)
        
    return filelist

def createSFReleaseFile(files):
    global config
    filetext = 'PACKAGE: unixname="%s": packagename="%s"\n' % (config.SF_UNIX_NAME, config.SF_PACKAGE_NAME)
    filetext += '  RELEASE: releasename="%s": releasenotes="%s": changes="%s"\n' % (config.SF_RELEASE_NAME, config.SF_RELEASE_NOTES, config.SF_CHANGES_FILE) 
    for afile in files:
        filetext += '    FILE: filename="%s": arch="Other"\n' % (afile)
    filetext += '  /RELEASE\n'
    filetext += '/PACKAGE\n'
    
    output = open("uploads", "w")
    output.write(filetext)
    output.close()

class Job(Job):
    LOGBASE = "./build_logs"

# ensure the staging area exists
if not os.path.exists(config.STAGING_DIR):
    os.makedirs(config.STAGING_DIR)

# Figure out the wxPython version number, possibly adjusted for being a daily build
if config.KIND == "daily":
    t = time.localtime()
    config.DAILY = time.strftime("%Y%m%d")   # should it include the hour too?  2-digit year?
    file("DAILY_BUILD", "w").write(config.DAILY)
    # stamp the date on daily builds
    config.BUILD_VERSION=config.BUILD_VERSION + "-" + config.DAILY
else:
    config.RELEASE_SFNAME=config.VERSION

# Let the user override build machine names, etc., etc. with their own
# config file settings
myconfig = None
myconfig_file = os.path.expanduser("~/eclass-release-environ.cfg")
if os.path.exists(myconfig_file):
    myconfig = Config()
    myconfig.read(myconfig_file)

# TODO: Set up different environs for daily, release, etc.
# so that people can have different configs for different builds

# prepare the environment file
config_env = config.asDict()
config_env.update(os.environ)
if myconfig:
    config_env.update(myconfig.asDict())
    
setup_tasks = Task([ Job("pre-flight", "./pre-flight.sh", env=config_env)]) 
start_time = time.time()
print "Build getting started at: ", time.ctime(start_time)


# Run the first task, which will create the docs and sources tarballs
tr = TaskRunner(setup_tasks)
rc = tr.run()

if "--strict" in sys.argv and rc != 0:
    sys.exit(1)
    
tasks = {}
wintasks = TaskRunner( Task([ Job("win", "./build-windows.sh", env=config_env), ]) )
tasks['win'] = wintasks

linuxtasks = TaskRunner( Task([ Job("linux", "./build-linux.sh", env=config_env), ]) )
tasks['linux'] = linuxtasks

intel_config = config_env.copy()
intel_config.update({"IS_INTEL":"yes"})

mactasks_intel = TaskRunner( Task([ Job("mac_intel", "./build-mac.sh", env=intel_config), ]) )
tasks['mac_intel'] = mactasks_intel

runtasks = ["win", "mac", "mac_intel"]

threads = []
for task in runtasks:
    newthread = TaskRunnerThread(tasks[task])
    newthread.start()
    threads.append(newthread)

isalive = True
for thread in threads:
    while isalive:
        isalive = False
        for thread in threads:
            if thread.isAlive():
                isalive=True
        time.sleep(1)

errorOccurred = False
for task in tasks:
    if tasks[task].rc != 0:
        print "Error occured during %s build tasks. Please check the error log." % task
        errorOccurred = True

if not errorOccurred and "upload" in sys.argv:
    releasefiles = getDistribFiles()
    createSFReleaseFile(releasefiles)

    upload_tasks = TaskRunner( Task([ Job("upload", "python2.4", ["sf-release.py", "uploads", config.SF_USERNAME.replace('"', ''), config.SF_PASSWORD.replace('"', '')], env=config_env), ]) )

    uploadthread = TaskRunnerThread(upload_tasks)
    uploadthread.start()

    while uploadthread.isAlive():
        time.sleep(1)

    if upload_tasks.rc != 0:
        errorOccurred = True
        print "Error occurred during upload tasks. Please check the error log."

if not errorOccurred and config.delete_temps == "yes":
    if os.path.exists(config.TEMP_DIR):
        shutil.rmtree(config.TEMP_DIR)
    if os.path.exists(config.STAGING_DIR):
        shutil.rmtree(config.STAGING_DIR)

# cleanup the DAILY_BUILD file
if config.KIND == "daily":
    for dist in os.listdir(config.DIST_DIR):
        # add the timestamp into the filename if it hasn't already been added
        if dist.find(config.BUILD_VERSION) == -1:
            newfile = dist.replace(config.VERSION, config.BUILD_VERSION)
            os.rename(os.path.join(config.DIST_DIR, dist), os.path.join(config.DIST_DIR, newfile))
    if os.path.exists("DAILY_BUILD"):
        os.unlink("DAILY_BUILD")
    
finish_time = time.time()
print "Build finished at: ", time.ctime(finish_time)
elapsed_time = finish_time-start_time
mins = elapsed_time/60
hours = mins/60
seconds = (elapsed_time - mins) % 60
print "Elapsed time: %d:%d:%d" % (hours, mins, seconds)

sys.exit(0)
