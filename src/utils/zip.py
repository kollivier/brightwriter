import sys, os

def dirToZipFile(dir, myzip, rootdir, excludeDirs=[], excludeFiles=[], zipDir=None, ignoreHidden=False):
    mydir = os.path.join(rootdir, dir)
    if not os.path.basename(dir) in excludeFiles:
        for file in os.listdir(mydir):
            mypath = os.path.join(mydir, file)
            if os.path.isfile(mypath) and not file in excludeFiles:
                if not ignoreHidden or not file[0] == ".":
                    # we use latin-1 because that is what WinZip defaults to
                    outputPath = os.path.join(dir, file)
                    if zipDir:
                        outputPath = os.path.join(zipDir, outputPath)
                    myzip.write(mypath, outputPath)
            elif os.path.isdir(mypath):
                dirToZipFile(os.path.join(dir, file), myzip, rootdir, 
                            excludeDirs, excludeFiles, zipDir, ignoreHidden)
