#!/bin/sh

DEST_DIR="$PWD/.."
ERROR=0
FORCE_INSTALL=0
SRC_DIR="$PWD"

if [ "$OSTYPE" = "cygwin" ]; then
    DEST_DIR="$DEST_DIR/win32"
elif [ "${OSTYPE:0:6}" = "darwin" ]; then
    DEST_DIR="$DEST_DIR/mac-intel"
else
    DEST_DIR="$DEST_DIR/linux"
fi

mkdir -p $DEST_DIR
echo $DEST_DIR

exitOnError(){
    if [ "$?" != 0 ]; then
        echo "Error occurred. Exiting."
        exit $?
    fi
}

install_prog(){
    NAME=$1
    TARBALL_PREFIX=$2
    CONF_FLAGS=$3
    MAKE_FLAGS=$4
    MAKE_INSTALL_FLAGS=$5

    if [ "$FORCE_INSTALL" = "1" ] || [ ! -d $DEST_DIR/$NAME ]; then
        TMP_DIR=/tmp/$NAME
        mkdir -p $TMP_DIR
        STARTDIR=$PWD
        
        cd $TMP_DIR
        TARBALL=$STARTDIR/$TARBALL_PREFIX.tar.gz
        if [ ! -f $TARBALL ]; then
            TARBALL=$STARTDIR/$TARBALL_PREFIX.tgz
        fi
        
        tar xzvf $TARBALL 
        cd $TARBALL_PREFIX
        
        if [ -f configure ]; then
            ./configure --prefix=$DEST_DIR/$NAME $CONF_FLAGS 
            exitOnError
        fi
        
        make clean
        make $MAKE_FLAGS
        exitOnError
        
        make install $MAKE_INSTALL_FLAGS
        exitOnError
        
        cd $STARTDIR
        rm -rf $TMP_DIR
        
        echo "Successfully installed $NAME."
    else
        echo "$NAME already installed."
    fi
}

if [ "$1" = "force" ]; then
    FORCE_INSTALL=1
fi

# install unrtf
install_prog "unrtf" "unrtf_0.20.2"

install_prog "wv" "wv-1.0.3"

install_prog "xlhtml" "xlhtml-0.4.9.3"
