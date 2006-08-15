#!/bin/sh

~/cx_Freeze-3.0.2/FreezePython --incldue-modules = encodings --install-dir deliver ../librarian.py
cp -r ../locale deliver