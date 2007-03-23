#!/bin/sh

# cleanup after old build files
#if [ -d $WX_TEMP_DIR ]; then
#  rm -rf $WX_TEMP_DIR
#fi 

START_DIR="$PWD"
rm -rf $DIST_DIR/*

ECLASS_TEMP_DIR=$TEMP_DIR/eclass_builder
# first, grab the latest revision with specified tag
if [ ! -d $TEMP_DIR ]; then
  mkdir $TEMP_DIR
fi 

cd $TEMP_DIR

# just do an update if we started a build but it failed somewhere
if [ ! -d $ECLASS_TEMP_DIR ]; then
    svn co https://eclass.svn.sourceforge.net/svnroot/eclass/trunk/eclass_builder
else
    cd $ECLASS_TEMP_DIR
    svn update
fi

# this is where we will store the wxAll tarball we create
if [ ! -d $DISTDIR ]; then
  mkdir $DISTDIR
fi

cd $ECLASS_TEMP_DIR

# generate docs
./installer/makedocs.sh
if [ $? != 0 ]; then
    echo "Making docs failed! Stopping release..."
    exit 1 
fi

# run unit tests
python2.4 runTests.py
if [ $? != 0 ]; then
    echo "Unit tests failed! Stopping release..."
    exit 1 
fi

if [ ! -d $ECLASS_TEMP_DIR/installer/deliver ]; then
  mkdir $ECLASS_TEMP_DIR/installer/deliver
fi

# Now generate the mega tarball with everything. We will push this to our build machines.

cd $TEMP_DIR
TARBALL=$TEMP_DIR/eclass.builder-$BUILD_VERSION.tar.gz
tar cvzf $TARBALL eclass_builder

echo "Tarball located at: $TARBALL"

if [ ! -f $TARBALL ]; then
  echo "ERROR: tarball was not created by pre-flight.sh. Build cannot continue."
  exit 1
else
  cd $START_DIR
  cp $TARBALL $STAGING_DIR

  echo "Pre-flight complete. Ready for takeoff."
fi
