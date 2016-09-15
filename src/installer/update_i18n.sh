#!/bin/sh

updatetrans(){
catalog=$1
sources=$2

for item in `find locale -name LC_MESSAGES`; do
    python installer/i18n/pygettext.py -d $catalog -a -p locale $sources
    # don't use fuzzy translations, as they're almost always bad guesses
    msgmerge -N $item/$catalog.po locale/$catalog.pot > $item/$catalog.po.new

    mv -f $item/$catalog.po.new $item/$catalog.po
    python installer/i18n/msgfmt.py $item/$catalog.po
done

}

rootdir=..
cd $rootdir

builder_sources="main.py editor.py conman/*.py gui/*.py plugins/*.py" 
updatetrans "eclass" "$builder_sources"

library_sources="eclass_library.py library/*.py library/gui/*.py"
updatetrans "library" "$library_sources"