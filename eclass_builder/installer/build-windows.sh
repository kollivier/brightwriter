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

    #ssh $WIN_HOST "cd $dir/3rdparty/win32 && unzip -o win32extras.zip"
    # run unit tests
    #ssh $WIN_HOST "cd $dir && python runTests.py"
    if [ $? != 0 ]; then
        echo "Unit tests failed! Stopping Windows release..."
        exit 1 
    fi

     cmd="cmd /c make_installer.bat $BUILD_VERSION"
     ssh $WIN_HOST "rm -rf $dir/installer/*.exe && cd $dir/installer && $cmd"

     echo "Fetching the results..."
     scp "$WIN_HOST:$dir/installer/eclass-builder-$BUILD_VERSION.exe "  $DIST_DIR

     echo "Done!"
fi
