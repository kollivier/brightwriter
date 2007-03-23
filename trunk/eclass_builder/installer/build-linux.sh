#!/bin/bash
#----------------------------------------------------------------------

set -o errexit

if [ $skiplinux != yes ]; then
    # test if the target machine is online
    #if ping -q -c1 $WIN_HOST > /dev/null; then
	#echo " The $WIN_HOST machine is online, Windows build continuing..."
    #else
	#echo "The $WIN_HOST machine is **OFFLINE**, skipping the Windows build."
	#exit 0
    #fi

    echo "Copying source file and build script..."
    scp -r $STAGING_DIR/* $LINUX_HOST:$LINUX_BUILD
    
     echo "Untarring dist on $LINUX_HOST..."
     tarball=$LINUX_BUILD/eclass.builder-$BUILD_VERSION.tar.gz
     cmd="tar xzvf"
     ssh $LINUX_HOST "cd $LINUX_BUILD && $cmd $tarball"
     
     echo "Running tarball build script on $LINUX_HOST..."
     dir=$LINUX_BUILD/eclass_builder
     cmd="rm -rf $dir/installer/deliver/* && cd $dir/installer && ./linux_build.sh"
     ssh $LINUX_HOST "$cmd"

     echo "Fetching the results..."
     scp "$LINUX_HOST:$dir/installer/deliver/*.tar.gz "  $DIST_DIR
     #scp "$LINUX_HOST:$wxdir/deliver/*.tar.bz2 "  $DIST_DIR
     
     echo "Done!"
fi