import os
import sys

def installEClassGettext():
    rootdir = sys.argv[0]
    if os.path.isfile(rootdir):
        rootdir = os.path.dirname(rootdir)
    localedir = os.path.join(os.path.abspath(rootdir), 'locale')
    print localedir
    import gettext
    gettext.install('eclass', localedir)
    lang_dict = {
                "en": gettext.translation('eclass', localedir, languages=['en']), 
                "es": gettext.translation('eclass', localedir, languages=['es']),
                "fr": gettext.translation('eclass', localedir, languages=['fr'])
                }

    return lang_dict
