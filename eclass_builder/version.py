#Version.py - controls the EClass Version

major = 3
minor = 0
release = 0
build_number = 6
build = "Preview %d" % build_number

def asString():
    return "%d.%d.%d %s" % (major, minor, release, build)
