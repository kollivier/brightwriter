import sys, os

def dirToZipFile(dir, myzip, rootdir, excludeDirs=[], excludeFiles=[], ignoreHidden=False):
    mydir = os.path.join(rootdir, dir)
    if not os.path.basename(dir) in excludeFiles:
        for file in os.listdir(mydir):
            mypath = os.path.join(mydir, file)
            if os.path.isfile(mypath) and not file in excludeFiles:
                if not ignoreHidden or not file[0] == ".":
                    # we use latin-1 because that is what WinZip defaults to
                    myzip.write(mypath.encode("utf-8"), os.path.join(dir, file).encode("utf-8"))
            elif os.path.isdir(mypath):
                dirToZipFile(os.path.join(dir, file), myzip, rootdir, 
                            excludeDirs, excludeFiles, ignoreHidden)