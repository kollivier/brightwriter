<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.0 Transitional//EN">
<html><head>
<title>--[name]--</title>
<meta name="description" content="--[description]--">
<meta name="keywords" content="--[keywords]--">
<meta name="URL" content="--[URL]--">
<script src="../APIWrapper.js"></script>
<script src="../SCOFunctions.js"></script>
<script type="text/javascript" language="JavaScript">
function expOpen(windowName)
{
	if (document.body)
	{
	explorer = window.open(windowName, "", "toolbar=yes,location=no,directories=no,status=no,menubar=no,scrollbars=yes,top=10,left=25,height=432,width=576");
	}
	else
	{
	explorer = window.open(windowName, "", "toolbar=yes,location=no,directories=no,status=no,menubar=no,scrollbars=yes,height=432,width=576");
	}
}

function openCredit(windowName, text)
{
	if (document.body)
	{
	explorer = window.open("",windowName,"toolbar=no,location=no,directories=no,status=no,menubar=yes,scrollbars=yes,top=10,left=25,height=200,width=200");
	}
	else
	{
	explorer = window.open("", windowName,"toolbar=no,location=no,directories=no,status=no,menubar=yes,scrollbars=yes,height=200,width=200");
	}
	
	var mydoc;
	mydoc = explorer.document;
	mydoc.open();
	mydoc.write("<HTML><HEAD></HEAD><BODY>" + text + "</BODY></HTML>");
	mydoc.close();
}

</script>
</head>
<body bgcolor="#FFFFF5" onload="loadPage()" onunload="doQuit('completed')">
<table id="exampletable" valign="top" width="100%">
  <tr valign="top">
<td width="0%">
		</td>
    <td width="100%">
<H1 align=center>--[name]--</H1>
--[content]--
<hr>
<table width="100%" cellpadding="0" cellspacing="0">
<tr>
<td width="5%" align="left">
<h5 align="left"></h5>
</td>
<td align="center">
<input type = "BUTTON" value = "  Next Page  " onClick = "doQuit('completed')" id=button2 name=button2>
--[credit]--
</td>
<td width="5%" align="right">
</td>
</tr>
</table>
<center></center>
    </td>
  </tr>
</table>
		</td>
	</tr>
</table>
</body></html>