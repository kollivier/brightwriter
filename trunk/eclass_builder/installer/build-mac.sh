#!/bin/bash
#----------------------------------------------------------------------

set -o errexit

if [ "$skipmac" != "yes" ]; then
     BUILD_TYPE=""
     PYTHON="/usr/local/bin/python"
     if [ "$IS_INTEL" == "yes" ]; then
         MAC_HOST=$MAC_HOST_INTEL
         BUILD_TYPE=""
         #PYTHON="python"
     fi
     # clean up the build dir
     ssh $MAC_HOST "rm -rf $MAC_BUILD/*"
     
     echo "Copying source file and build script..."
     scp -r $STAGING_DIR/* $MAC_HOST:$MAC_BUILD
    
     echo "Untarring dist on $MAC_HOST..."
     tarball=$MAC_BUILD/eclass.builder-$BUILD_VERSION.tar.gz
     cmd="tar xzvf"
     ssh $MAC_HOST "cd $MAC_BUILD && $cmd $tarball"
     
     echo "Running build script on $MAC_HOST..."
     dir=$MAC_BUILD/trunk/eclass_builder
     
     # run unit tests
     ssh $MAC_HOST "cd $dir"

     cmd="$PYTHON make-installer.py"
     ssh $MAC_HOST "cd $dir/installer && rm -rf build dist && $cmd"

     DMG_DIR=$DIST_DIR/dmg_files

     mkdir -p $DMG_DIR
     scp -r "$MAC_HOST:$dir/installer/dist/EClass.Builder.app "  $DMG_DIR
     #cd $OLDDIR

     DMG_NAME=./deliver/eclass-builder-$BUILD_VERSION.dmg
     if [ -f $DMG_NAME ]; then
       rm $DMG_NAME
     fi
     
     hdiutil create -srcfolder $DMG_DIR -volname "EClass.Builder" -imagekey zlib-level=9 $DMG_NAME
     
     rm -rf $DMG_DIR

     echo "Fetching the results..."
     ssh $MAC_HOST "rm -rf $STAGING_DIR/*"
     #hdiutil attach $DMG_NAME
     
     #cp -r deliver/EClass.Builder.app /Volumes/EClass.Builder
     
     #hdiutil detach /Volumes/EClass.Builder
     
     echo "Done!"
fi
