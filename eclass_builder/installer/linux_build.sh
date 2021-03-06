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
cp -r ../locale librarian-linux
cp -r ../library/pages librarian-linux
cp -r ../library/templates = librarian-linux

cgibin=librarian-linux/librarian-cgi
echo "#!/bin/sh" > $cgibin
echo "" >> $cgibin
echo "export LD_LIBRARY_PATH=." >> $cgibin
echo "exec ./librarian" >> $cgibin
chmod +x $cgibin

mkdir -p deliver
tar czvf deliver/librarian-linux.tar.gz librarian-linux
