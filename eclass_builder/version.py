#Version.py - controls the EClass Version

major = 3
minor = 0
release = 0
build = "preview1"

def asString():
    return `major` + "." + `minor` + "." + `release` + "-" + `build`
