[Setup]
AppName=CustomFolder
AppVersion=0.0.1
AppPublisher=Ceziy
DefaultDirName={pf}\CustomFolder
DefaultGroupName=CustomFolder
OutputBaseFilename=CustomFolderInstaller
Compression=lzma
SolidCompression=yes
WizardStyle=modern
OutputDir=installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Registry]
Root: HKCR; Subkey: "Directory\shell\CustomFolder"; ValueType: string; ValueName: ""; ValueData: "Сменить иконку"; Flags: uninsdeletekey
Root: HKCR; Subkey: "Directory\shell\CustomFolder\command"; ValueType: string; ValueName: ""; ValueData: """{app}\CustomFolder.exe"" ""%1"""; Flags: uninsdeletekey


[Files]
Source: "output/CustomFolder.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "./folder.png"; DestDir: "{app}"; Flags: ignoreversion

[UninstallRun]
Filename: "taskkill"; Parameters: "/f /im CustomFolder.exe /t"; Flags: runhidden waituntilterminated

[Code]
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usUninstall then
  begin
    RegDeleteKeyIncludingSubkeys(HKCR, 'Directory\shell\CustomFolder');
  end;
end;

[Dirs]
Name: "{app}"; Permissions: everyone-full