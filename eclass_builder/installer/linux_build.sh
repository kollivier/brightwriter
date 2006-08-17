#!/bin/sh

# This part is needed for cx_Freeze 3.0.3 to work
# can be removed when cx_Freeze has a better method for importing
# all encodings.
prefix=`python2.4 -c "import sys; print sys.prefix"`
echo "import encodings" > ../encodings_import.py
for line in `ls $prefix/lib/python2.4/encodings/*.py`; do
    encoding=`basename ${line/.py}`
    echo "import encodings.$encoding" >> ../encodings_import.py
done

~/cx_Freeze-3.0.3/FreezePython  --include-modules=encodings_import --install-dir librarian-linux ../librarian.py
cp -r ../locale librarian-cgi-linux
mkdir -p deliver
tar czvf librarian-linux.tar.gz librarian-linux
