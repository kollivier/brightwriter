#!/bin/bash

dir=$1

if [ ! -d $dir ]; then
    dir=..
    cd $dir
fi

tarball=$dir/eclass.builder-$BUILD_VERSION.tar.gz

if [ -f $tarball ]; then
    tar xzvf $tarball
    cd $dir/brightwriter
fi 

/usr/local/bin/python2.4 runTests.py

if [ $? != 0 ]; then
    echo "Unit tests failed! Stopping Mac release..."
    exit 1 
fi

cd $dir/installer 
rm -rf build dist

export PYTHONPATH=.. 
/usr/local/bin/python2.4 make_builder_osx.py py2app 
/usr/local/bin/python2.4 make_library_osx.py py2app