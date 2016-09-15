import sys, os
from ReleaseForge import sf
from ReleaseForge import FileVO
from ReleaseForge.constants import *

debug = True

class Release:
    def __init__(self, project="", packagename="", releasename=""):
        self.project = project
        self.packagename = packagename
        self.releasename = releasename
        self.files = []

# this is needed for upload_files to work
class FakeParent:
    def isCancelled(self):
        return False

def makeDict(list):
    adict = {}   
    for item in list:
        name, val = item.strip().split("=")
        name = name.strip()
        val = val.strip().replace('"', '')
        adict[name] = val
        
    return adict
            

def get_uploads_by_release(filename):
    project = ""
    package = ""
    release = None
    releases = []
    data = open(filename, "r").readlines()
    for line in data:
        fields = line.split(":")
        if fields[0].strip() == "PACKAGE":
            info = makeDict(fields[1:])
            project = info['unixname']
            package = info['packagename']
            
        elif fields[0].strip() == "RELEASE":
            if project == "" or package == "":
                print "Parse Error. File has no project, package, or release info."
                sys.exit(1)
            info = makeDict(fields[1:])
            release = info['releasename']
            releasenotes = info['releasenotes']
            changes = info['changes']
            release = Release(project, package, release)
        elif fields[0].strip() == "FILE":
            info = makeDict(fields[1:])
            if release == None:
                print "Parse error. No release information for file %s." % (info['filename'])
                sys.exit(1)
            
            filename = info['filename']
            arch = info['arch']
            if os.path.exists(filename):
                ext = os.path.splitext(filename)[1]
                filetype = FILE_TYPE_GUESS[ext]
                filevo = FileVO.FileVO(filename, os.path.basename(filename), 
                      arch, CPU[arch], filetype, FILE_TYPE[filetype],
                      None)
            
                release.files.append(filevo)

        elif fields[0].strip() == "/RELEASE":
            if release == None:
                print "Parse error. /RELEASE tag found when no current release."
                sys.exit(1)
                
            releases.append(release)
            release = None
        else:
            if debug:
                print "Field 0 = " + `fields[0].strip()`

    return releases 
        

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print "Usage: sf-release.py <uploads_file> <sf-username> <sf-password>\n\n"
        print "Uploads files to sourceforge.net and adds the release information\n"
        print "based on the information in <uploads_file>. See uploads_sample for\n"
        print "a sample info file."
        sys.exit(1)
        
    releases = get_uploads_by_release(sys.argv[1])
        
    sf_username = sys.argv[2]
    sf_password = sys.argv[3]
    
    datadir = "./" # do we want to make this changeable?
    # connect to SourceForge.net and login
    try:
        sf_link = sf.SF(datadir, username=sf_username, password=sf_password)
    except:
        import traceback
        print `traceback.print_exc()`
        print "Could not login to SourceForge, update aborted."
        sys.exit(1)

    if debug:
        print "len(releases) = " + `len(releases)`

    for arelease in releases:
        #see if the project can be accessed with this user/pass        
        for proj in sf_link.projects:
            groupid = ""
            packageid = ""
            releaseid = ""
            
            if arelease.project == proj.getUnixName():
                groupid = proj.getGroupId()
                if debug:
                    print "Found SF project for release..."
                
                #now find the package id...
                for package in proj.getPackages():
                    if arelease.packagename == package.getPackageName():
                        packageid = package.getPackageId()
                        if debug:
                            print "Found release package..."
                        
            if groupid != "" and packageid != "":
                # proceed to create or find the release, then
                # upload the files.
                
                sf_releases = sf_link.sf_comm.get_releases(groupid, packageid)
                for sf_release in sf_releases:
                    if sf_release[0].strip() == arelease.releasename:
                        releaseid = sf_release[1].strip()
                
                if releaseid == "" and sf_link.sf_comm.can_create_releases(groupid):
                    # we need to create the new release
                    releaseid = sf_link.sf_comm.add_release(groupid, packageid, 
                                    arelease.releasename)
                    
                    if releaseid != "":
                        print "Created new release: " + arelease.releasename

                parent = FakeParent()
                msg = sf_link.sf_comm.upload_files(parent, arelease.files)
                print msg
                if msg.find("FTP error") != -1:
                    sys.exit(1)
                print "File(s) uploaded..."
                
                # update the release to contain the files 
                files_dict, warnings, ok = sf_link.sf_comm.edit_release_step2(groupid, 
                                                   packageid, releaseid,
                                                   arelease.files)

                if ok:
                    ok = sf_link.sf_comm.edit_release_step3(groupid, packageid, releaseid,
                                                   arelease.files, files_dict)
                    
                if ok:
                    print "Release %s updated successfully." % (arelease.releasename)
        # upload file to SF
        # run through the add_release... edit_release forms