!define MUI_PRODUCT "EClass.Builder" ;Define your own software name here
!define MUI_VERSION "2.5.4.17" ;Define your own software version here
!include "${NSISDIR}\Contrib\Modern UI\System.nsh"
!include "path_functions.nsi"
!define MUI_ICON "${NSISDIR}\contrib\Icons\new_nsis_2.ico"
!define MUI_UNICON "${NSISDIR}\contrib\Icons\new_nsis_2.ico"
;--------------------------------
;Configuration
  !define MUI_LICENSEPAGE
  ;!define MUI_COMPONENTSPAGE
  !define MUI_DIRECTORYPAGE
  !define MUI_ABORTWARNING
  !define MUI_UNINSTALLER
  !define MUI_UNCONFIRMPAGE
  ;Language
  !insertmacro MUI_LANGUAGE "English"
  
  ;General
  OutFile "eclass-builder-${MUI_VERSION}.exe"

  ;License page
  LicenseData "..\license\License.txt"

  ;Descriptions
  LangString DESC_SecCopyUI ${LANG_ENGLISH} "Install the EClass.Builder Application"

  ;Folder-selection page
  InstallDir "$PROGRAMFILES\${MUI_PRODUCT} ${MUI_VERSION}"

;--------------------------------
;Modern UI System

!insertmacro MUI_SYSTEM

;--------------------------------
;Installer Sections
Section "Program Files" SecCopyUI
  SetShellVarContext "all"
  ;ADD YOUR OWN STUFF HERE!
  WriteRegStr HKLM SOFTWARE\EClass\Builder\${MUI_VERSION} "Path" "$INSTDIR"
  SetOutPath "$INSTDIR"
  File /r "..\3rdparty\win32\gre\*"
  ;WriteRegStr HKLM SOFTWARE\mozilla.org\GRE\wxMozilla\1.3 "GreHome" "$PROGRAMFILES\Common Files\mozilla.org\GRE\wxMozilla\1.3"
  ;Push "$PROGRAMFILES\Common Files\mozilla.org\GRE\wxMozilla\1.3"
  ;Call AddToPath
  File "disteditor\*.*"
  File "editor.exe.manifest"
  File "..\converter.py"
  File "..\swishe.conf"
  File /r "..\convert"
  File /r "..\about"
  File /r "..\autorun"
  File /r "..\Greenstone"
  File /r "..\docs"
  File /r "..\icons"
  File /r "..\license"
  File /r "..\locale"
  File /r "..\cgi-bin"

  SetOutPath "$INSTDIR\plugins"
  File "..\plugins\__init__.py"
  File "..\plugins\eclass.py"
  File "..\plugins\quiz.py"
  File "..\plugins\html.py"
  File /r "..\plugins\Quiz"

  SetOutPath "$INSTDIR\themes"
  File "..\themes\__init__.py"
  File "..\themes\BaseTheme.py"
  File "..\themes\Default_frames.py"
  File "..\themes\Default_no_frames.py"
  File /r "..\themes\Default (Frames)"
  File /r "..\themes\Default (No Frames)"
  File /r "..\themes\ThemePreview"

  SetOutPath "$INSTDIR\3rdparty\win32"
  File "C:\Python23\w9xpopen.exe"
  File /r "..\3rdparty\win32\htmldoc"
  File /r "..\3rdparty\win32\karrigell"
  File /r "..\3rdparty\win32\SWISH-E"
  CreateDirectory "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}"
  SetOutPath $INSTDIR ; for working directory
  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\Uninstall ${MUI_PRODUCT} ${MUI_VERSION}.lnk" "$INSTDIR\Uninstall.exe"

  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\EClass.Builder.lnk" "$INSTDIR\editor.exe"

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "DisplayName" "${MUI_PRODUCT} ${MUI_VERSION} (remove only)"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "UninstallString" '"$INSTDIR\Uninstall.exe"'

SectionEnd
;Section "OpenOffice Support"
;	IfFileExists $PROGRAMFILES\OpenOffice.org1.1Beta\program\*.* 0 NoOpenOffice
;		SetOutPath $PROGRAMFILES\OpenOffice.org1.1Beta\program
;		File /r "..\pyuno\*.*"
;		ExecWait "$PROGRAMFILES\OpenOffice.org1.1Beta\program\pyuno_setup.bat"
;		Push "$PROGRAMFILES\OpenOffice.org1.1Beta\program"
; 		Call AddToPath
;		Push "$PROGRAMFILES\OpenOffice.org1.1Beta\program"
;		Call AddToPythonPath
;		ExecWait '"$INSTDIR\editor.exe" --autostart-pyuno'
;		Return
;	NoOpenOffice:
;		MessageBox MB_OK "Could not find an existing OpenOffice 1.1 beta installation. OpenOffice support will not be enabled."
;SectionEnd
;Display the Finish header
;Insert this macro after the sections if you are not using a finish page
!insertmacro MUI_SECTIONS_FINISHHEADER
;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTIONS_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecCopyUI} $(DESC_SecCopyUI)
!insertmacro MUI_FUNCTIONS_DESCRIPTION_END
 
;--------------------------------
;Uninstaller Section

Section "Uninstall"
  SetShellVarContext "all"
  ;ADD YOUR OWN STUFF HERE!

  RMDir /r "$INSTDIR"

  RMDir /r "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}" 
;  DeleteRegKey HKLM SOFTWARE\mozilla.org\GRE\wxMozilla\1.3
;  Push "$PROGRAMFILES\Common Files\mozilla.org\GRE\wxMozilla\1.3"
;  Call un.RemoveFromPath
  DeleteRegKey HKLM SOFTWARE\EClass\Builder\${MUI_VERSION}
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}"
;  Push "$PROGRAMFILES\OpenOffice.org1.1Beta\program"
;  Call un.RemoveFromPath
;  Push "$PROGRAMFILES\OpenOffice.org1.1Beta\program"
;  Call un.RemoveFromPythonPath
  ;Display the Finish header
  !insertmacro MUI_UNFINISHHEADER

SectionEnd