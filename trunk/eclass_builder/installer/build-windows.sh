#!/bin/bash
#----------------------------------------------------------------------

set -o errexit

if [ $skipwin != yes ]; then
    
    ssh $WIN_HOST "rm -rf $WIN_BUILD/*"
    
    echo "Copying source file and build script..."
    scp -r $STAGING_DIR/* $WIN_HOST:$WIN_BUILD
    
     echo "Untarring dist on $WIN_HOST..."
     tarball=$WIN_BUILD/eclass.builder-$BUILD_VERSION.tar.gz
     cmd="tar xzvf"
     ssh $WIN_HOST "cd $WIN_BUILD && $cmd $tarball"
     
     echo "Running build script on $WIN_HOST..."
     dir=$WIN_BUILD/eclass_builder
     cmd="export VS71COMNTOOLS=$MSVS7_DIR/Common7/Tools/ && cmd /c make_installer.bat $BUILD_VERSION"
     #cmd="/c/python23/python ../updateVersion.py && python2.4 make_py_dist.py && /c/Progra~1/nsis/makensis eclass-builder.nsi"
     #scp ./make_msvc7_setup $WIN_HOST:$dir/installer
     #&& export MSVS7_DIR=$MSVS7_DIR && export NET_FrameworkDir=$NET_FrameworkDir && . make_msvc7_setup
     ssh $WIN_HOST "rm -rf $dir/installer/*.exe && cd $dir/installer && $cmd"

     echo "Fetching the results..."
     scp "$WIN_HOST:$dir/installer/eclass-builder-$BUILD_VERSION-unicode.exe "  $DIST_DIR

     echo "Done!"
fi