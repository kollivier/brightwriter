#!/bin/bash
#----------------------------------------------------------------------

set -o errexit

if [ "$skipmac" != "yes" ]; then
     BUILD_TYPE="ppc"
     PYTHON="python"
     if [ "$IS_INTEL" == "yes" ]; then
         MAC_HOST=$MAC_HOST_INTEL
         BUILD_TYPE="intel"
         #PYTHON="python"
     fi
     echo "Copying source file and build script..."
     scp -r $STAGING_DIR/* $MAC_HOST:$MAC_BUILD
    
     echo "Untarring dist on $MAC_HOST..."
     tarball=$MAC_BUILD/eclass.builder-$BUILD_VERSION.tar.gz
     cmd="tar xzvf"
     ssh $MAC_HOST "cd $MAC_BUILD && $cmd $tarball"
     
     echo "Running build script on $MAC_HOST..."
     dir=$MAC_BUILD/eclass_builder
     
     # run unit tests
     ssh $MAC_HOST "cd $dir" # && $PYTHON runTests.py"
     #if [ $? != 0 ]; then
     #    echo "Unit tests failed! Stopping release..."
     #    exit 1 
     #fi

     cmd="export PYTHONPATH=..:/Users/kevino/wxpython-2.8/wxPython/wx-2.8-mac-unicode && $PYTHON make_builder_osx.py py2app --no-strip" # && $PYTHON make_library_osx.py py2app --no-strip"
     ssh $MAC_HOST "cd $dir/installer && rm -rf build dist && $cmd"

     # now it's time for 'fun fixing the PyXML hacks!'
     #OLDDIR=$PWD
     APP_PYDIR=$dir/installer/dist/EClass.Builder.app/Contents/Resources/lib/python2.4
     #if [ "$IS_INTEL" != "yes" ]; then
     #    ssh $MAC_HOST "cd $APP_PYDIR && mv lib-dynload/xml/parsers/pyexpat.so lib-dynload && mv lib-dynload/xml/parsers/sgmlop.so lib-dynload"
     #    ssh $MAC_HOST "zip $APP_PYDIR/site-packages.zip -d xml/*"
     #    ssh $MAC_HOST "cd /Library/Frameworks/Python.framework/Versions/2.4/lib/python2.4 && zip -r -g -n .pyc $APP_PYDIR/site-packages.zip . -i xml\*.pyc && cd site-packages && zip -r -g -n .pyc:.mo $APP_PYDIR/site-packages . -i _xmlplus\*.pyc _xmlplus\*.mo"
     #fi

     mkdir -p $DIST_DIR/dmg_files-$BUILD_TYPE
     scp -r "$MAC_HOST:$dir/installer/dist/EClass.Builder.app "  $DIST_DIR/dmg_files-$BUILD_TYPE
     #cd $OLDDIR

     DMG_NAME=deliver/eclass-builder-$BUILD_VERSION-$BUILD_TYPE.dmg
     DMG_DIR=$DIST_DIR/dmg_files-$BUILD_TYPE
     if [ -f $DMG_NAME ]; then
       rm $DMG_NAME
     fi
     
     hdiutil create -srcfolder $DIST_DIR/dmg_files-$BUILD_TYPE -volname "EClass.Builder" -imagekey zlib-level=9 $DMG_NAME
     
     rm -rf $DMG_DIR

     #scp -r "$MAC_HOST:$dir/installer/dist/EClass.Library.app "  $DMG_DIR
     #DMG_NAME=deliver/eclass-library-$LIBRARY_VERSION-$BUILD_TYPE.dmg
     #if [ -f $DMG_NAME ]; then
     #  rm $DMG_NAME
     #fi
     
     #hdiutil create -srcfolder $DMG_DIR -volname "EClass.Library" -imagekey zlib-level=9 $DMG_NAME
     
     rm -rf $DMG_DIR

     echo "Fetching the results..."
     ssh $MAC_HOST "rm -rf $STAGING_DIR/*"
     #hdiutil attach $DMG_NAME
     
     #cp -r deliver/EClass.Builder.app /Volumes/EClass.Builder
     
     #hdiutil detach /Volumes/EClass.Builder
     
     echo "Done!"
fi
