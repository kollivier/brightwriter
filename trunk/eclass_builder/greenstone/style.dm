#######################################################################
# PAGE STYLES 
#######################################################################

package Style

# to use this style system output
# _header_
# all your page content, then
# _footer_

# use the page parameter 'style' to choose the appropriate style

# the style system uses
# _pagetitle_  - what gets displayed at the top of the browser window
# _pagescriptextra_ - any extra javascript you want included in the header
# _pagebannerextra_ - anything extra you want displayed in the page banner
# _pagefooterextra_ - anything extra you want displayed in the footer

# defaults for the above macros
_pagetitle_ {_collectionname_}
_pagescriptextra_ {}
_pagebannerextra_ {}
_pagefooterextra_ {}

# it also relies on lots of Globals, the most important of these are:
# _cookie_ - put in the cgi header
# _globalscripts_ - javascript stuff
# _httpiconchalk_ - the image down the left of the page
# _imagecollection_
# _imagehome_
# _imagehelp_
# _imagepref_
# _imagethispage_
# _linkotherversion_

_header_ {_cgihead_
_htmlhead__startspacer__pagebanner_
}

_header_[v=1] {_cgihead_
_htmlhead__pagebanner_
}

# _cgihead_ {Content-type: text/html
# _cookie_
#
# }	
_cgihead_{}

# htmlhead uses:
# _1_ - extra parameters for the body tag
# _pagetitle_
# _globalscripts_
_htmlhead_ {
<html_htmlextra_>
<head>
<title>_pagetitle_</title>
_globalscripts_
</head>

<body bgcolor="\#ffffff" text="\#000000" link="\#006666" 
      alink="\#cc9900" vlink="\#666633"_1_>
}


# _startspacer_ is a spacer to get past the 10010 graphic. It contains an open
# <table> tag which must eventually be closed by _endspacer_.
_startspacer_ {
<table border=0 cellspacing=0 cellpadding=0 width="100%">
<tr><td valign=top width=65><img src="_httpimg_/spacer.gif" width="65" height="1" alt="" border="0"></td>
<td><center><table width="_pagewidth_"><tr><td>
}


# pagebanner uses :
# _imagecollection_ 
# _imagehome_
# _imagehelp_
# _imagepref_
# _imagethispage_
# _pagebannerextra_
_pagebanner_ {
<!-- page banner (\_style:pagebanner\_) -->
<center>
<table width=_pagewidth_ cellspacing=0 cellpadding=0>
  <tr valign=top>
    <td rowspan=2 align=left>_imagecollection_</td>
    <td align=right>_javalinks_</td>
  </tr>

  <tr>
    <td align=right>_imagethispage_</td>
  </tr>

  <tr>
    <td colspan=2>_pagebannerextra_</td>
  </tr>
</table>
</center>
<!-- end of page banner -->
}

_pagebanner_[v=1] {
<!-- page banner - text version [v=1] (\_style:pagebanner\_) -->
<center><h2><b><u>_imagecollection_</u></b></h2></center><p>
_javalinks_
_pagebannerextra_
<p>
<!-- end of page banner -->
}

_footer_ {
<!-- page footer (\_style:footer\_) -->
_pagefooterextra_
</table>
_endspacer__htmlfooter_
}

_endspacer_ {</center>
</td></tr></table>
}

_htmlfooter_ {
</body>
</html>
}

_globalscripts_{
<script>
<!--
_imagescript_
_pagescriptextra_
// -->
</script>
}

_globalscripts_ [v=1] {
<script>
<!--
_If_(_cgiargx_,_scriptdetach_)
_pagescriptextra_
// -->
</script>
}

_scriptdetach_ {
    function close\_detach() \{
	close();
    \}
}
