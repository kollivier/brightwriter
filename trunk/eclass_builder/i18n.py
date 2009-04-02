import os

def installEClassGettext():
    rootdir = os.path.join(os.path.dirname(__file__))
    localedir = os.path.join(os.path.abspath(rootdir), 'locale')
    import gettext
    gettext.install('eclass', localedir)
    lang_dict = {
                "en": gettext.translation('eclass', localedir, languages=['en']), 
                "es": gettext.translation('eclass', localedir, languages=['es']),
                "fr": gettext.translation('eclass', localedir, languages=['fr'])
                }

    return lang_dict
