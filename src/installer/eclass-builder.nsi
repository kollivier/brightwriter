!define MUI_PRODUCT "BrightWriter" ;Define your own software name here
!define MUI_VERSION "2.5.5.14" ;Define your own software version here
!define UNICODE_STRING "" ; for unicode, add unicode the the installer name
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
  OutFile "eclass-builder-${MUI_VERSION}${UNICODE_STRING}.exe"

  ;License page
  LicenseData "..\license\License.txt"

  ;Descriptions
  LangString DESC_SecCopyUI ${LANG_ENGLISH} "Install the BrightWriter Application"

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
  File /r "dist\*"

  CreateDirectory "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}"
  SetOutPath $INSTDIR ; for working directory
  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\Uninstall ${MUI_PRODUCT} ${MUI_VERSION}.lnk" "$INSTDIR\Uninstall.exe"

  CreateShortCut "$SMPROGRAMS\${MUI_PRODUCT} ${MUI_VERSION}\BrightWriter.lnk" "$INSTDIR\brightwriter.exe"

  ;Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "DisplayName" "${MUI_PRODUCT} ${MUI_VERSION} (remove only)"

  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}" "UninstallString" '"$INSTDIR\Uninstall.exe"'

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
  DeleteRegKey HKLM SOFTWARE\EClass\Builder\${MUI_VERSION}
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\${MUI_PRODUCT} ${MUI_VERSION}"

SectionEnd
