!include MUI2.nsh

!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

Name 'Util paisagem'

# define name of installer
OutFile "Util_Paisagem_Installer.exe"
 
# define installation directory
InstallDir "$LOCALAPPDATA\Programs\Util Paisagem"
 
# For removing Start Menu shortcut in Windows 7
RequestExecutionLevel user
 
# start default section
Section
 
    # set the installation directory as the destination for the following actions
    SetOutPath $INSTDIR

    File /r dist\nsis\*.*
    CreateShortcut "$SMPROGRAMS\Util Paisagem.lnk" "$INSTDIR\Util_paisagem.bat" "" #"$INSTDIR\resources\util paisagem.ico" 0 SW_SHOWMINIMIZED
 
    # create the uninstaller
    WriteUninstaller "$INSTDIR\uninstall.exe"
 
    # create a shortcut named "new shortcut" in the start menu programs directory
    # point the new shortcut at the program uninstaller
    CreateShortcut "$SMPROGRAMS\Util Paisagem uninstaller.lnk" "$INSTDIR\uninstall.exe"
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
