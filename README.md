# BrightWriter

BrightWriter is a cross-platfrom app for the creation of e-books. It contains a set of tools
that simplify e-book development and assist in the creation of educational e-books that follow
Instructional Design principles.

# Building BrightWriter

## Requirements

Python 3.6

## Getting Started

After checking out the source code, setup your environment for building BrightWriter.

### (Optional, but recommended) Install virtualenv and create a virtualenv for BrightWriter

    pip install virtualenv
    virtualenv bwenv

### Install pip dependencies 

    pip install -f requirements-{platform}.txt

### Install wxPython Phoenix

    pip install --upgrade --trusted-host wxpython.org --pre -f http://wxpython.org/Phoenix/snapshot-builds/ wxPython_Phoenix 

#### (Mac only) Enable your virtualenv to run Python.app to start the wxPython GUI
    cp deps/mac/pythonw bwenv/bin/
    chmod +x bwenv/bin/pythonw

