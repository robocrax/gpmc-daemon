<#
  Builds the GPMC Windows app.

    powershell -ExecutionPolicy Bypass -File windows\build.ps1

  Output in dist\:
    GPMC\                 the app folder (GPMC.exe + syncthing\syncthing.exe)
    GPMC-portable.zip     the same folder, zipped
    GPMC-Setup.exe        per-user installer (needs Inno Setup 6; installed automatically in CI)

  Options:
    -Python <exe>           Python to use (default: python)
    -SyncthingVersion <v>   Syncthing release to bundle (default below)
    -SkipPip                don't install Python packages (already installed)
#>
param(
  [string]$Python = "python",
  [string]$SyncthingVersion = "v2.1.7",
  [switch]$SkipPip
)

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Step($msg) { Write-Host "==> $msg" -ForegroundColor Cyan }
function Run($exe, [string[]]$argv) {
  & $exe @argv
  if ($LASTEXITCODE -ne 0) { throw "$exe exited with $LASTEXITCODE" }
}

if (-not $SkipPip) {
  Step "Installing Python packages"
  Run $Python @("-m", "pip", "install", "--disable-pip-version-check", "-q", "-r", "requirements.txt", "-r", "windows\requirements.txt")
}

Step "Generating icon and version info"
$assetOut = & $Python windows\make_assets.py
if ($LASTEXITCODE -ne 0) { throw "make_assets.py failed" }
$Version = ($assetOut | Select-Object -Last 1).Trim()
Write-Host "    version $Version"

Step "Fetching Syncthing $SyncthingVersion"
$dl = Join-Path $Root "windows\build\syncthing-$SyncthingVersion"
New-Item -ItemType Directory -Force $dl | Out-Null
$zipName = "syncthing-windows-amd64-$SyncthingVersion.zip"
$base = "https://github.com/syncthing/syncthing/releases/download/$SyncthingVersion"
$zip = Join-Path $dl $zipName
$sums = Join-Path $dl "sha256sum.txt.asc"
if (-not (Test-Path $zip)) { Invoke-WebRequest "$base/$zipName" -OutFile $zip -UseBasicParsing }
Invoke-WebRequest "$base/sha256sum.txt.asc" -OutFile $sums -UseBasicParsing
$line = Select-String -Path $sums -Pattern ([regex]::Escape($zipName)) | Select-Object -First 1
if (-not $line) { throw "No checksum listed for $zipName" }
$want = ($line.Line -split "\s+")[0].ToLower()
$got = (Get-FileHash $zip -Algorithm SHA256).Hash.ToLower()
if ($want -ne $got) { throw "Syncthing checksum mismatch: expected $want, got $got" }
Write-Host "    checksum ok"
$unz = Join-Path $dl "unzipped"
if (Test-Path $unz) { Remove-Item -Recurse -Force $unz }
Expand-Archive $zip -DestinationPath $unz
$stDir = Get-ChildItem $unz -Directory | Select-Object -First 1

Step "Building GPMC.exe with PyInstaller"
if (Test-Path dist\GPMC) { Remove-Item -Recurse -Force dist\GPMC }
Run $Python @("-m", "PyInstaller", "--noconfirm", "--clean", "--log-level", "WARN",
  "--distpath", "dist", "--workpath", "windows\build\pyinstaller", "windows\gpmc.spec")

Step "Adding Syncthing and licences"
$app = Join-Path $Root "dist\GPMC"
New-Item -ItemType Directory -Force "$app\syncthing", "$app\licenses" | Out-Null
Copy-Item (Join-Path $stDir.FullName "syncthing.exe") "$app\syncthing\"
Copy-Item (Join-Path $stDir.FullName "LICENSE.txt") "$app\licenses\syncthing-LICENSE.txt"
Copy-Item LICENSE* "$app\licenses\" -ErrorAction SilentlyContinue
$licScript = @'
import importlib.metadata as md, shutil, sys
dest = sys.argv[1]
for dist in ("gpmc", "pystray", "fastapi", "uvicorn", "pillow", "pillow_heif"):
    try:
        files = md.distribution(dist).files or []
    except md.PackageNotFoundError:
        continue
    for f in files:
        name = f.name.upper()
        if name.startswith(("LICENSE", "LICENCE", "COPYING", "NOTICE")):
            shutil.copy(f.locate(), f"{dest}/{dist}-{f.name}")
'@
$licScript | & $Python - "$app\licenses"
Copy-Item windows\THIRD-PARTY-NOTICES.txt "$app\licenses\"

Step "Zipping portable build"
if (Test-Path dist\GPMC-portable.zip) { Remove-Item dist\GPMC-portable.zip }
Compress-Archive -Path $app -DestinationPath dist\GPMC-portable.zip

Step "Building installer"
$iscc = @(
  "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
  "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
  "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
if (-not $iscc -and $env:CI) {
  choco install innosetup -y --no-progress | Out-Host
  $iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
}
if ($iscc -and (Test-Path $iscc)) {
  Run $iscc @("/Q", "/DAppVersion=$Version", "windows\installer.iss")
  Write-Host "    dist\GPMC-Setup.exe"
} else {
  Write-Warning "Inno Setup 6 not found; skipped GPMC-Setup.exe (the portable zip is ready)."
}

Step "Done: GPMC $Version"
Get-ChildItem dist -File | Format-Table Name, @{n = "MB"; e = { [math]::Round($_.Length / 1MB, 1) } } -AutoSize | Out-Host
