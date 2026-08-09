!include MUI2.nsh

!define APP_NAME "Util Paisagem"
!define APP_VERSION "0.5.0rc1"
!define APP_ICON "resources\images\utilpaisagem.ico"
!define MUI_ICON "${APP_ICON}"
!define MUI_UNICON "${APP_ICON}"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

!define MUI_ABORTWARNING

Name "${APP_NAME} ${APP_VERSION}"

# define name of installer
OutFile "dist\Util_Paisagem_Installer.exe"

ShowInstDetails show
ShowUninstDetails show
 
# define installation directory
InstallDir "$LOCALAPPDATA\Programs\${APP_NAME}"
 
# For removing Start Menu shortcut in Windows 7
RequestExecutionLevel user

# start default section
Section
 
    # set the installation directory as the destination for the following actions
    SetOutPath $INSTDIR

    File /r dist\nsis\*.*

    CreateShortcut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\pythonw.exe" "run.py" "$INSTDIR\resources\images\utilpaisagem.ico"; 0 SW_SHOWMINIMIZED
    ; CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    ; CreateShortcut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\Util_paisagem.bat" "" "$INSTDIR\resources\images\utilpaisagem.ico" 0 SW_SHOWMINIMIZED
    ; CreateShortcut "$SMPROGRAMS\${APP_NAME}\Get the latest version.lnk" "https://github.com/leandroarndt/util-paisagem/releases/latest" "" "$INSTDIR\resources\images\utilpaisagem.ico"
    ; CreateShortcut "$SMPROGRAMS\${APP_NAME}\Using ${APP_NAME}.lnk" "https://github.com/leandroarndt/util-paisagem/wiki/usage" "" "$INSTDIR\resources\images\utilpaisagem.ico"
 
    # create the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
 
    # create a shortcut named "new shortcut" in the start menu programs directory
    # point the new shortcut at the program uninstaller
    CreateShortcut "$SMPROGRAMS\Uninstall ${APP_NAME}.lnk" "$INSTDIR\uninstall.exe" "" "$INSTDIR\resources\images\utilpaisagem.ico"

    WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "DisplayName" "${APP_NAME}"
    WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "UninstallString" '"$INSTDIR\uninstall.exe"'
    WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "InstallLocation" "$INSTDIR"
    WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "DisplayIcon" "$INSTDIR\${APP_ICON}"
    WriteRegStr SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "DisplayVersion" "${APP_VERSION}"
    WriteRegDWORD SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "NoModify" 1
    WriteRegDWORD SHCTX "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APP_NAME}" \
                    "NoRepair" 1
SectionEnd
 
# uninstaller section start
Section "uninstall"
 
    Delete "$INSTDIR\*.*"
	# first, delete the uninstaller
    # Delete "$INSTDIR\uninstall.exe"
 
    # second, remove the link from the start menu
	Delete "$SMPROGRAMS\Util Paisagem.lnk"
    Delete "$SMPROGRAMS\Util Paisagem uninstaller.lnk"
 
    RMDir /r $INSTDIR
# uninstaller section end
SectionEnd
