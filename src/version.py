#Version.py - controls the EClass Version

major = 1
minor = 0
release = 0
build_number = 2
build = "Preview %d" % build_number

def asString():
    return "%d.%d.%d %s" % (major, minor, release, build)
