#!/bin/sh

# cleanup after old build files
#if [ -d $WX_TEMP_DIR ]; then
#  rm -rf $WX_TEMP_DIR
#fi 

START_DIR="$PWD"
rm -rf $DIST_DIR/*

ECLASS_TEMP_DIR=$TEMP_DIR/brightwriter
# first, grab the latest revision with specified tag
if [ ! -d $TEMP_DIR ]; then
  mkdir $TEMP_DIR
fi 

cd $TEMP_DIR

if [ -d $ECLASS_TEMP_DIR ]; then
    rm -rf $ECLASS_TEMP_DIR
fi

if [ -d $STAGING_DIR ]; then
    rm -rf $STAGING_DIR
fi

svn co https://eclass.svn.sourceforge.net/svnroot/eclass/trunk/brightwriter

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

if [ ! -d $ECLASS_TEMP_DIR/installer/deliver ]; then
  mkdir $ECLASS_TEMP_DIR/installer/deliver
fi

# Now generate the mega tarball with everything. We will push this to our build machines.

cd $TEMP_DIR
TARBALL=$TEMP_DIR/eclass.builder-$BUILD_VERSION.tar.gz
tar cvzf $TARBALL brightwriter

echo "Tarball located at: $TARBALL"

if [ ! -f $TARBALL ]; then
  echo "ERROR: tarball was not created by pre-flight.sh. Build cannot continue."
  exit 1
else
  cd $START_DIR
  cp $TARBALL $STAGING_DIR

  echo "Pre-flight complete. Ready for takeoff."
fi
