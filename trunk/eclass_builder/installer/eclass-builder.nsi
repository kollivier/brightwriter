!define MUI_PRODUCT "EClass.Builder" ;Define your own software name here
!define MUI_VERSION "2.5.5.2" ;Define your own software version here
Name "${MUI_PRODUCT} ${MUI_VERSION}"
!include "MUI.nsh"
!include "path_functions.nsi"
!define MUI_ICON "${NSISDIR}\contrib\Graphics\Icons\classic-install.ico"
!define MUI_UNICON "${NSISDIR}\contrib\Graphics\Icons\classic-uninstall.ico"
;--------------------------------
;Configuration
  !insertmacro MUI_PAGE_DIRECTORY
  !insertmacro MUI_PAGE_INSTFILES
  !insertmacro MUI_PAGE_FINISH

  !define MUI_ABORTWARNING
  
  ;!define MUI_UNINSTALLER
  !insertmacro MUI_UNPAGE_CONFIRM
  !insertmacro MUI_UNPAGE_INSTFILES
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

  Var "hasDM"

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
  File /r "minipython\*"
  File "editor.exe"
  File "editor.exe.manifest"
  File "..\*.py"
  File "..\bookfile.book.in"
  File /r "..\conman"
  File /r "..\convert"
  File /r "..\about"
  File /r "..\autorun"
  File /r "..\Greenstone"
  File /r "..\docs"
  File /r "..\icons"
  File /r "..\installers"
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
  File "..\themes\themes.py"
  File "..\themes\BaseTheme.py"
  File "..\themes\Default_frames.py"
  File "..\themes\Default_no_frames.py"
  File "..\themes\IMS_Package.py"
  File /r "..\themes\Default (Frames)"
  File /r "..\themes\Default (No Frames)"
  File /r "..\themes\ThemePreview"
  File /r "..\themes\IMS Package"

  SetOutPath "$INSTDIR\3rdparty\win32"
  File "C:\Python23\w9xpopen.exe"
  File /r "..\3rdparty\win32\htmldoc"
  ;File /r "..\3rdparty\win32\karrigell"
  ;File /r "..\3rdparty\win32\SWISH-E"
  CreateDirectory "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}"
  SetOutPath $INSTDIR ; for working directory
  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\Uninstall ${MUI_PRODUCT} ${MUI_VERSION}.lnk" "$INSTDIR\Uninstall.exe"

  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\EClass.Builder.lnk" "$INSTDIR\editor.exe"

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "DisplayName" "${MUI_PRODUCT} ${MUI_VERSION} (remove only)"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "UninstallString" '"$INSTDIR\Uninstall.exe"'

  EnumRegKey $hasDM HKLM "Software\Vaclav Slavik\Documancer" 0
  StrCmp "$hasDM" "" CheckHKCU CheckForDM
CheckHKCU:
  EnumRegKey $hasDM HKCU "Software\Vaclav Slavik\Documancer" 0
  StrCmp "$hasDM" "" InstallDM CheckForDM
CheckForDM:
  StrCmp "$hasDM" "0.2.4" Finished InstallDM  
InstallDM:
  Exec $INSTDIR\installers\documancer-0.2.4-setup.exe

Finished:
SectionEnd

;--------------------------------
;Descriptions

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecCopyUI} $(DESC_SecCopyUI)
!insertmacro MUI_FUNCTION_DESCRIPTION_END
 
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

SectionEnd