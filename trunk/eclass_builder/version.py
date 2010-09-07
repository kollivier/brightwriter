#Version.py - controls the EClass Version

major = 3
minor = 0
release = 0
build = "Preview 1"

def asString():
    return "%d.%d.%d %s" % (major, minor, release, build)
