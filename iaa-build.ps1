#Requires -Version 5.1
param(
    [string]$Backend = "pyinstaller"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 验证后端参数
if ($Backend -notin @("pyinstaller", "nuitka")) {
    Write-Error "Invalid backend: $Backend. Supported backends: pyinstaller, nuitka"
    exit 1
}

# 路径与常量
$buildDir = 'build'
$distDir = 'dist_app'
$exeName = 'iaa.exe'
$iconPath = 'assets/icon_round.ico'

# 解析版本与时间戳
$content = Get-Content 'pyproject.toml' -Raw
$m = [regex]::Match($content, '^[\s]*version[\s]*=[\s]*"([^"]+)"', 'Multiline')
$version = if ($m.Success) { $m.Groups[1].Value } else { '0.0.0' }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'

# 根据是否有 7z 命令决定文件扩展名
$has7z = Get-Command 7z -ErrorAction SilentlyContinue
$packageName = "iaa_v$version" + "_" + "$stamp" + $(if ($has7z) { ".7z" } else { ".zip" })

Write-Host "Backend: $Backend"
Write-Host "Version: $version"
Write-Host "Timestamp: $stamp"
Write-Host "Output: $packageName"

Remove-Item -Recurse -Force $distDir -ErrorAction SilentlyContinue

# 根据后端选择构建方式
if ($Backend -eq "pyinstaller") {
    Write-Host "Building with PyInstaller..."
    
    # PyInstaller 构建参数
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
    
    # 执行 PyInstaller
    & python -m PyInstaller @pyinstallerArgs
    
    # PyInstaller 产物路径
    $appName = $exeName.Replace('.exe', '')
    $builtDir = Join-Path $buildDir $appName
    $builtExePath = Join-Path $builtDir "$appName.exe"
    
} elseif ($Backend -eq "nuitka") {
    Write-Host "Building with Nuitka..."
    
    # Nuitka 构建
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
    
    # Nuitka 产物路径
    $builtDir = Join-Path $buildDir "launch_desktop.dist"
    $builtExePath = Join-Path $builtDir $exeName
}

# 检查构建是否成功
if (-not (Test-Path $builtExePath)) {
    Write-Error "Build failed: executable not found at $builtExePath"
    exit 1
}

    $appName = $exeName.Replace('.exe', '')
    $builtDir = Join-Path $buildDir $appName
    $builtExePath = Join-Path $builtDir "$appName.exe"

# 创建发布目录并复制执行文件
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $distDir 'assets') | Out-Null
Copy-Item -Recurse -Force (Join-Path $builtDir '*') $distDir

# 复制资源：assets 与 iaa/res -> assets/res_compiled
Copy-Item -Recurse -Force 'assets/*' (Join-Path $distDir 'assets')
$resDestDir = Join-Path $distDir 'assets/res_compiled'
New-Item -ItemType Directory -Force -Path $resDestDir | Out-Null
Copy-Item -Recurse -Force 'iaa/res/*' $resDestDir


# 压缩打包（优先 7z；否则使用 Compress-Archive）
Write-Host "Creating package..."
if ($has7z) {
    Push-Location $distDir
    # 使用 7z 格式，最大压缩等级 (mx=9)
    & 7z a -t7z -mx=9 "../$packageName" * | Out-Null
    Pop-Location
} else {
    if (Test-Path $packageName) { Remove-Item -Force $packageName }
    # 使用最大压缩等级
    Compress-Archive -Path "$distDir/*" -DestinationPath $packageName -CompressionLevel Optimal
}

Write-Host "Packaged: $packageName"
Write-Host "Build completed successfully using $Backend backend!" 