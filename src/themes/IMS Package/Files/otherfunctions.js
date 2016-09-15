/*****************************************************************************
**
** The Boeing Company grants you ("Licensee") a non-exclusive, royalty free, 
** license to use, modify and redistribute this software in source and binary 
** code form, provided that 
**   i) this copyright notice and license appear on all copies of the software; and 
**  ii) Licensee does not utilize the software in a manner which is disparaging 
**      to The Boeing Company.
**
** This software is provided "AS IS," without a warranty of any kind.  ALL
** EXPRESS OR IMPLIED CONDITIONS, REPRESENTATIONS AND WARRANTIES, INCLUDING ANY
** IMPLIED WARRANTY OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE OR NON-
** INFRINGEMENT, ARE HEREBY EXCLUDED.  The Boeing Company AND ITS LICENSORS 
** SHALL NOT BE LIABLE FOR ANY DAMAGES SUFFERED BY LICENSEE AS A RESULT OF USING,
** MODIFYING OR DISTRIBUTING THE SOFTWARE OR ITS DERIVATIVES.  IN NO EVENT WILL 
** The Boeing Company OR ITS LICENSORS BE LIABLE FOR ANY LOST REVENUE, PROFIT OR
** DATA, OR FOR DIRECT, INDIRECT, SPECIAL, CONSEQUENTIAL, INCIDENTAL OR PUNITIVE
** DAMAGES, HOWEVER CAUSED AND REGARDLESS OF THE THEORY OF LIABILITY, ARISING 
** OUT OF THE USE OF OR INABILITY TO USE SOFTWARE, EVEN IF The Boeing Company 
** HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
**
* Copyright Unpublished - 2002.  All rights reserved under the copyright        *
* laws by The Boeing Company.                                                   *
*******************************************************************************/

/* |  otherfunctions.js
/* |  Version 1.0
/* |  Author: Brandt Dargue, Boeing
/**/
function get_params()
{
   var strSearch = window.location.search;
   var idx = strSearch.indexOf('?');
   if (idx != -1) 
   {
      var pairs = strSearch.substring(idx+1, strSearch.length).split('&');
      for (var i=0; i<pairs.length; i++) 
      {
         nameVal = pairs[i].split('=');
         g_params[nameVal[0]] = nameVal[1];
      }
   }
}

/* *********************************************************************** */
/*  IETM/D functions                                                       */    
/* *********************************************************************** */
function OpenWindow(url, width, height, options)
{
     //this is  default width if no width is defined when function is called   
     if (!width) width = 950;   
     //this is default height if no width is defined when function is called 
     if (!height) height = 700;  
     if (!options) 
     {     
        //default options if no options are defined when the function is called
        options = "left=50,top=50,scrollbars=yes,menubar=no,toolbar=no,location=no,status=no,resizable=yes"; 
     }
     if(!myPopupWindow || myPopupWindow.closed) 
     {  
        myPopupWindow = window.open( url, "popupWindow",
        "width=" + width + ",height=" + height + "," + options );
     }
    if (!myPopupWindow.opener) 
    {
       newwin.opener = self;
    }
    myPopupWindow.focus();
}
