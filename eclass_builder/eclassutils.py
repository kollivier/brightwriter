import os
import shutil
import unittest

import ims.contentpackage
import ims.utils
import constants
import version

import htmlutils
import plugins
import utils

import externals.BeautifulSoup as bs


def createEClass(dirname):
    # create the EClass folders
    os.mkdir(dirname)
    for dir in constants.eclassdirs:
        subdir = os.path.join(dirname, dir)
        if not os.path.exists(subdir):
            os.mkdir(subdir)

    return EClass(os.path.join(dirname, "imsmanifest.xml"))


def getEClassPageForIMSResource(imsresource):
    # for EClass pages, the source page is listed as a dependency of the generated
    # HTML page. This is so that tools that do not understand the EClass Page format
    # can read EClass-created IMS content packages.
    filename = None
    if imsresource:
        for file in imsresource.files:
            if "href" in file.attrs and os.path.splitext(file.attrs["href"])[1] == ".ecp":
                filename = file.attrs["href"]

    return filename


def IMSHasEClassPages(imspackage):
    for resource in imspackage.resources:
        if getEClassPageForIMSResource(resource):
            return True

    return False


def IMSRemoveEClassPages(imspackage):
    for resource in imspackage.resources:
        for file in resource.files:
            if "href" in file.attrs and os.path.splitext(file.attrs["href"])[1] == ".ecp":
                resource.files.remove(file)


def getEditableFileForIMSItem(imscp, imsitem):
    filename = None
    if imsitem:
        selresource = ims.utils.getIMSResourceForIMSItem(imscp, imsitem)
        if selresource:
            filename = selresource.getFilename()
            eclasspage = getEClassPageForIMSResource(selresource)
            if eclasspage:
                filename = eclasspage

    return filename


def setEClassPageForIMSResource(imsresource, filename):
    # for EClass pages, the source page is listed as a dependency of the generated
    # HTML page. This is so that tools that do not understand the EClass Page format
    # can read EClass-created IMS content packages.
    plugin = plugins.GetPluginForFilename(filename)
    publisher = plugin.HTMLPublisher()
    filelink = publisher.GetFileLink(filename)

    # Assign the .html page as the page seen by IMS package readers
    imsresource.setFilename(filelink)

    # Now make the .ecp file a dependency so that EClass knows to
    # use the .ecp file instead of the .html file
    imsfile = ims.contentpackage.File()
    imsfile.attrs["href"] = filename
    imsresource.files.append(imsfile)


def getResourceNamespace():
    return u"URN:IMS-PLIRID-V0:"


def getItemUUIDWithNamespace():
    return getResourceNamespace() + utils.getUUID()


def updateManifestLinkedFiles(imsresource, htmlfile, html):
    basedir = os.path.dirname(htmlfile)
    soup = bs.BeautifulSoup(html)
    hrefs = soup.findAll(href=True)
    links = []
    for href in hrefs:
        url = href['href']
        links.append(url)

    srcs = soup.findAll(src=True)
    for src in srcs:
        url = src['src']
        links.append(url)

    pub_links = []
    for link in links:
        abspath = link
        if not os.path.isabs(link):
            abspath = os.path.join(basedir, link)

        # ignore links that don't point to on disk resources
        if os.path.exists(abspath):
            # FIXME: Eventually we want to strip the publication root from the filename and add on
            # any subdirs above the HTML page that aren't in the link.
            if basedir.endswith("Content") and not link.startswith("Content"):
                link = "Content/" + link

            pub_links.append(link)

    files_to_remove = []
    for afile in imsresource.files:
        if not afile.attrs['href'] in pub_links:
            files_to_remove.append(afile)

    for afile in files_to_remove:
        imsresource.files.remove(afile)

    for link in pub_links:
        has_file = False
        for file in imsresource.files:
            if file.attrs['href'] == link:
                has_file = True

        if not has_file:
            imsfile = ims.contentpackage.File()
            imsfile.attrs["href"] = link
            imsfile.attrs['id'] = str(uuid.uuid4())
            imsresource.files.append(imsfile)


class EClass:
    """
    The purpose of this class is to handle issues specific to EClass
    that do not necessarily fall under IMSCP functionality. Such as
    creating and managing .ecp files, while still making the output
    100% IMSCP-compatibile.
    """
    def __init__(self, filename):
        self.filename = filename
        self.imscp = ims.contentpackage.ContentPackage()
        if os.path.exists(self.filename):
            self.imscp.loadFromXML(self.filename)

        generator = ims.contentpackage.Contributor()
        generator.role.source["x-none"] = "LOMv1.0"
        generator.role.value["x-none"] = "Creator"
        generator.centity.vcard = "BEGIN:vCard FN:EClass Builder v%s END:vCard" % version.asString()

        self.imscp.metadata.lom.metametadata.contributors.append(generator)

    def saveAsIMSCP(self, filename=None):
        self.imscp.saveAsXML(self.filename)


class EClassTests(unittest.TestCase):
    def testCreateEClass(self):
        import tempfile
        tempdir = tempfile.mkdtemp()
        eclassdir = os.path.join(tempdir, "testEClass")
        createEClass(eclassdir)

        for adir in constants.eclassdirs:
            self.assert_(os.path.exists(os.path.join(eclassdir, adir)))

        shutil.rmtree(tempdir)


def getTestSuite():
    return unittest.makeSuite(EClassTests)

if __name__ == '__main__':
    unittest.main()
