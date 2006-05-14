// loader.cpp : Defines the entry point for the application.
//

#include "stdafx.h"
#include <windows.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <memory.h>
#include <shellapi.h>

int APIENTRY WinMain(HINSTANCE hInstance,
                     HINSTANCE hPrevInstance,
                     LPSTR     lpCmdLine,
                     int       nCmdShow)
{
 	HKEY regKey;
	bool hasDM = false;

	if (::RegOpenKeyEx(HKEY_LOCAL_MACHINE, TEXT("Software\\Vaclav Slavik\\Documancer"), 0, KEY_QUERY_VALUE, &regKey) == ERROR_SUCCESS){
		hasDM = true;
	}
	else if (::RegOpenKeyEx(HKEY_CURRENT_USER, TEXT("Software\\Vaclav Slavik\\Documancer"), 0, KEY_QUERY_VALUE, &regKey) == ERROR_SUCCESS){
		hasDM = true;
	}

	if (hasDM){
		HINSTANCE result = ShellExecute(0, "open", "eclass.dmbk", "", "", SW_SHOWMAXIMIZED);
		if ((long)result < 32)
			hasDM = false;
	}
	
	if (!hasDM){
		SHELLEXECUTEINFO si;
		memset(&si, 0, sizeof(si));
		si.cbSize = sizeof(si);
		si.hwnd = NULL;
		si.lpVerb = "open";
		si.lpFile = "installers\\documancer-0.2.6-setup.exe";
		si.nShow = SW_NORMAL;
		si.fMask = SEE_MASK_NOCLOSEPROCESS | SEE_MASK_FLAG_NO_UI;
		bool res = ShellExecuteEx(&si);
		if (res){
			WaitForSingleObject(si.hProcess,
								INFINITE);
			//now it's installed, try it again
			ShellExecute(0, "open", "eclass.dmbk", "", "", SW_SHOWMAXIMIZED);
		}
		else{
			ShellExecute(0, "open", "index.html", "", "", SW_SHOWMAXIMIZED);
		}
	}

	return 0;
}



