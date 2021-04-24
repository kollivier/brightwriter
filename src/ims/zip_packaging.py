import logging
import os
import shutil
import tempfile
import zipfile

import utils.zip as zip_utils


def export_package_as_zip(project_dir, zip_filename=None):
    tempdir = tempfile.mkdtemp()
    try:
        imsdir = os.path.dirname(os.path.join(tempdir, "IMSPackage"))
        if not os.path.exists(imsdir):
            os.makedirs(imsdir)

        handle, zipname = tempfile.mkstemp()
        os.close(handle)
        if zip_filename and os.path.exists(zip_filename):
            os.remove(zip_filename)

        assert os.path.exists(project_dir)

        myzip = zipfile.ZipFile(zipname, "w")
        zip_utils.dirToZipFile("", myzip, project_dir,
                               excludeDirs=["installers", "cgi-bin"], ignoreHidden=True)

        myzip.close()
        if zip_filename:
            os.rename(zipname, zip_filename)
        else:
            zip_filename = zipname
    finally:
        # Don't treat tempdir deletion as a fatal error.
        if tempdir and os.path.exists(tempdir):
            try:
                shutil.rmtree(tempdir, ignore_errors=True)
            except:
                import traceback
                logging.warning(traceback.format_exc())

    return zip_filename
