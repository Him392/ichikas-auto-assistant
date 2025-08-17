#Requires -Version 5.1
param(
    [string]$Backend = "pyinstaller"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# ��֤��˲���
if ($Backend -notin @("pyinstaller", "nuitka")) {
    Write-Error "Invalid backend: $Backend. Supported backends: pyinstaller, nuitka"
    exit 1
}

# ·���볣��
$buildDir = 'build'
$distDir = 'dist_app'
$exeName = 'iaa.exe'
$iconPath = 'assets/icon_round.ico'

# �����汾��ʱ���
$content = Get-Content 'pyproject.toml' -Raw
$m = [regex]::Match($content, '^[\s]*version[\s]*=[\s]*"([^"]+)"', 'Multiline')
$version = if ($m.Success) { $m.Groups[1].Value } else { '0.0.0' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# �����Ƿ��� 7z ��������ļ���չ��
$has7z = Get-Command 7z -ErrorAction SilentlyContinue
$packageName = "iaa_v$version" + "_" + "$stamp" + $(if ($has7z) { ".7z" } else { ".zip" })

Write-Host "Backend: $Backend"
Write-Host "Version: $version"
Write-Host "Timestamp: $stamp"
Write-Host "Output: $packageName"

Remove-Item -Recurse -Force $distDir -ErrorAction SilentlyContinue

# ���ݺ��ѡ�񹹽���ʽ
if ($Backend -eq "pyinstaller") {
    Write-Host "Building with PyInstaller..."
    
    # PyInstaller ��������
    $currentDir = Get-Location
    $assetsPath = Join-Path $currentDir "assets"
    $fullIconPath = Join-Path $currentDir $iconPath
    $pyinstallerArgs = @(
        "--onedir",
        # "--windowed",
        "--icon=$fullIconPath",
        "--distpath=$buildDir",
        "--workpath=$(Join-Path $buildDir 'work')",
        "--specpath=$(Join-Path $buildDir 'spec')",
        "--name=$($exeName.Replace('.exe', ''))",
        # "--add-data=$assetsPath;assets",
        "--hidden-import=rapidocr_onnxruntime",
        "--hidden-import=kotonebot", 
        "--hidden-import=kaa",
        "--hidden-import=iaa.res",
        "--hidden-import=iaa.res.sprites",
        "--collect-all=rapidocr_onnxruntime",
        "--collect-all=kotonebot",
        "--collect-all=kaa",
        "--noconfirm",
        "launch_desktop.py"
    )
    
    # ִ�� PyInstaller
    & python -m PyInstaller @pyinstallerArgs
    
    # PyInstaller ����·��
    $appName = $exeName.Replace('.exe', '')
    $builtDir = Join-Path $buildDir $appName
    $builtExePath = Join-Path $builtDir "$appName.exe"
    
} elseif ($Backend -eq "nuitka") {
    Write-Host "Building with Nuitka..."
    
    # Nuitka ����
    & python -m nuitka `
        --standalone `
        --assume-yes-for-downloads `
        --enable-plugin=tk-inter `
        --windows-icon-from-ico=$iconPath `
        --output-dir=$buildDir `
        --output-filename=$exeName `
        --include-package-data=rapidocr_onnxruntime `
        --include-package-data=kotonebot `
        --include-package-data=kaa `
        launch_desktop.py
    
    # Nuitka ����·��
    $builtDir = Join-Path $buildDir "launch_desktop.dist"
    $builtExePath = Join-Path $builtDir $exeName
}

# ��鹹���Ƿ�ɹ�
if (-not (Test-Path $builtExePath)) {
    Write-Error "Build failed: executable not found at $builtExePath"
    exit 1
}

    $appName = $exeName.Replace('.exe', '')
    $builtDir = Join-Path $buildDir $appName
    $builtExePath = Join-Path $builtDir "$appName.exe"

# ��������Ŀ¼������ִ���ļ�
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $distDir 'assets') | Out-Null
Copy-Item -Recurse -Force (Join-Path $builtDir '*') $distDir

# ������Դ��assets �� iaa/res -> assets/res_compiled
Copy-Item -Recurse -Force 'assets/*' (Join-Path $distDir 'assets')
$resDestDir = Join-Path $distDir 'assets/res_compiled'
New-Item -ItemType Directory -Force -Path $resDestDir | Out-Null
Copy-Item -Recurse -Force 'iaa/res/*' $resDestDir


# ѹ����������� 7z������ʹ�� Compress-Archive��
Write-Host "Creating package..."
if ($has7z) {
    Push-Location $distDir
    # ʹ�� 7z ��ʽ�����ѹ���ȼ� (mx=9)
    & 7z a -t7z -mx=9 "../$packageName" * | Out-Null
    Pop-Location
} else {
    if (Test-Path $packageName) { Remove-Item -Force $packageName }
    # ʹ�����ѹ���ȼ�
    Compress-Archive -Path "$distDir/*" -DestinationPath $packageName -CompressionLevel Optimal
}

Write-Host "Packaged: $packageName"
Write-Host "Build completed successfully using $Backend backend!" 