package home

#######################################################################
# java images/scripts
#######################################################################

# the _javalinks_ macros are the flashy image links at the top right of
# the page. this is overridden here as we don't want 'home' 
# links on this page

_javalinks_ {}
_javalinks_ [v=1] {}

#######################################################################
# icons
#######################################################################

_iconselectcollection_ {<img align=texttop src="_httpiconselcolgr_" width=_widthselcolgr_ height=_heightselcolgr_ alt=_altselcolgr_>}
_iconmusiclibrary_ {<img align=texttop src="_httpicontmusic_" border=1 alt="meldex music library">}

#######################################################################
# http macros 
#
# These contain the url without any quotes
#######################################################################

_httppagegsdl_ {_httppagex_(gsdl)}
_httppagehomehelp_ {_httppagex_(homehelp)}


#######################################################################
# images
#######################################################################


_imagecollector_ {_gsimage_(_httppagecollector_,_httpimg_/ccolof.gif,_httpimg_/ccolon.gif,col,_collector:textcollector_)}
_imageadmin_ {_gsimage_(_httppagestatus_,_httpimg_/cadminof.gif,_httpimg_/cadminon.gif,admin,_textadmin_)}
_imagegogreenstone_ {_gsimage_(_home:httppagegsdl_,_httpimg_/cabgsof.gif,_httpimg_/cabgson.gif,gogs,_textabgs_)}
_imagegodocs_ {_gsimage_(_home:httppagedocs_,_httpimg_/cgsdocof.gif,_httpimg_/cgsdocon.gif,docs,_textgsdocs_)}
_imagehelp_ {_gsimage_(_home:httppagehomehelp_,_httpiconchelpof_,_httpiconchelpon_,help,_textimagehelp_)}

#######################################################################
# page content                     
#######################################################################

_content_ {
<h1 align="center"><a href="eclass/index.htm">Start E-Class</a></h1>
}
