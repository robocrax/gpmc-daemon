; Inno Setup script for the GPMC Windows installer.
; Built by windows/build.ps1:  ISCC /DAppVersion=x.y.z windows\installer.iss
; Per-user install (no admin prompt) into %LOCALAPPDATA%\Programs\GPMC.
; User data in %LOCALAPPDATA%\GPMC (accounts, photo queue) is kept on uninstall.

#ifndef AppVersion
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1C2B7E-4D5A-4E8B-9C3F-2A7D1E5B8C40}
AppName=GPMC
AppVersion={#AppVersion}
AppVerName=GPMC {#AppVersion}
AppPublisher=Robocrax
AppPublisherURL=https://robocrax.github.io/gpmc-daemon/
AppSupportURL=https://github.com/robocrax/gpmc-daemon/issues
AppUpdatesURL=https://github.com/robocrax/gpmc-daemon/releases
DefaultDirName={localappdata}\Programs\GPMC
DisableDirPage=auto
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=GPMC-Setup
SetupIconFile=build\gpmc.ico
UninstallDisplayIcon={app}\GPMC.exe
UninstallDisplayName=GPMC
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no

[Tasks]
Name: "autostart"; Description: "Start GPMC when I sign in to Windows (recommended, so backups keep running)"
Name: "desktopicon"; Description: "Add a desktop shortcut"; Flags: unchecked

[Files]
Source: "..\dist\GPMC\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{userprograms}\GPMC"; Filename: "{app}\GPMC.exe"; Comment: "Back up your phone's photos to Google Photos"
Name: "{userdesktop}\GPMC"; Filename: "{app}\GPMC.exe"; Tasks: desktopicon

[Registry]
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "GPMC"; ValueData: """{app}\GPMC.exe"" --background"; Tasks: autostart

[Run]
Filename: "{app}\GPMC.exe"; Description: "Open GPMC now"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\GPMC.exe"; Parameters: "--quit"; Flags: runhidden waituntilterminated; RunOnceId: "QuitGPMC"

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { Upgrading: ask a running copy to exit so its files can be replaced. }
  if FileExists(ExpandConstant('{app}\GPMC.exe')) then
    Exec(ExpandConstant('{app}\GPMC.exe'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;

procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  { The tray menu can turn sign-in start on later, so always clear it. }
  if CurUninstallStep = usPostUninstall then
    RegDeleteValue(HKEY_CURRENT_USER, 'Software\Microsoft\Windows\CurrentVersion\Run', 'GPMC');
end;
