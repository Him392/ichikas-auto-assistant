#Requires -Version 5.1
param(
    [string]$Backend = "pyinstaller",
    [Alias('BuildDiffUpdate')][switch]$BuildDiff
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# 验证后端参数
if ($Backend -notin @("pyinstaller", "nuitka")) {
    Write-Error "Invalid backend: $Backend. Supported backends: pyinstaller, nuitka"
    exit 1
}

# 路径与常量
$repoRoot = (Get-Location).Path
$buildDir = 'build'
$distDirBase = 'dist_app'
$exeName = 'iaa.exe'
$iconPath = 'assets/icon_round.ico'

# 解析版本与时间戳
$content = Get-Content 'pyproject.toml' -Raw
$m = [regex]::Match($content, '^[\s]*version[\s]*=[\s]*"([^"]+)"', 'Multiline')
$version = if ($m.Success) { $m.Groups[1].Value } else { '0.0.0' }
$stamp = Get-Date -Format 'yyyy-MM-dd-HH-mm-ss'

# 将版本写入 iaa/__meta__.py 供运行时读取
$initPath = 'iaa/__meta__.py'
$initContent = @"
__VERSION__ = "$version"
"@
Set-Content -Path $initPath -Value $initContent -Encoding UTF8

# 根据是否有 7z 命令决定文件扩展名
$has7z = Get-Command 7z -ErrorAction SilentlyContinue
$packageName = "iaa_v$version" + "_" + "$stamp" + $(if ($has7z) { ".7z" } else { ".zip" })

# 版本输出目录（dist_app/{版本号_时间戳}）
$versionInfo = "v$version" + "_" + "$stamp"
$distDir = Join-Path $distDirBase $versionInfo

Write-Host "Backend: $Backend"
Write-Host "Version: $version"
Write-Host "Timestamp: $stamp"
Write-Host "Output package: $packageName"
Write-Host "Dist directory: $distDir"

# 仅清理当前版本输出目录，保留历史版本用于差异比较
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
        "--hidden-import=uiautomator2",
        "--collect-all=rapidocr_onnxruntime",
        "--collect-all=kotonebot",
        "--collect-all=kaa",
        "--collect-all=uiautomator2",
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
        --include-package-data=uiautomator2 `
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

# 创建发布目录并复制执行文件
New-Item -ItemType Directory -Force -Path $distDir | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $distDir 'assets') | Out-Null
Copy-Item -Recurse -Force (Join-Path $builtDir '*') $distDir

# 复制资源：assets 与 iaa/res -> assets/res_compiled
Copy-Item -Recurse -Force 'assets/*' (Join-Path $distDir 'assets')
$resDestDir = Join-Path $distDir 'assets/res_compiled'
New-Item -ItemType Directory -Force -Path $resDestDir | Out-Null
Copy-Item -Recurse -Force 'iaa/res/*' $resDestDir

# 压缩打包（优先 7z；否则使用 Compress-Archive），显示压缩输出
Write-Host "Creating package..."
$packageOutputPath = Join-Path $repoRoot $packageName
if ($has7z) {
    Push-Location $distDir
    # 使用 7z 格式，最大压缩等级 (mx=9)
    & 7z a -t7z -mx=2 $packageOutputPath *
    Pop-Location
} else {
    if (Test-Path $packageOutputPath) { Remove-Item -Force $packageOutputPath }
    # 使用最大压缩等级
    Compress-Archive -Path "$distDir/*" -DestinationPath $packageOutputPath -CompressionLevel Optimal
}

Write-Host "Packaged: $packageOutputPath"
Write-Host "Build completed successfully using $Backend backend!" 

# 若启用差异更新包，比较上一个版本并打包差异
if ($BuildDiff) {
    Write-Host "Building diff update package..."
    if (-not (Test-Path $distDirBase)) {
        Write-Warning "BuildDiff: 未找到历史输出目录 $distDirBase"
    } else {
        $currentResolved = (Resolve-Path $distDir).Path
        $candidates = Get-ChildItem -Path $distDirBase -Directory | Where-Object { (Resolve-Path $_.FullName).Path -ne $currentResolved }
        $prev = $candidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        if (-not $prev) {
            Write-Warning "BuildDiff: 未找到上一个版本目录用于比较"
        } else {
            $prevDir = $prev.FullName
            Write-Host "BuildDiff: Comparing with previous version: $prevDir"

            $currentFiles = Get-ChildItem -Path $distDir -Recurse -File
            $diffRelPaths = @()
            foreach ($cf in $currentFiles) {
                $rel = $cf.FullName.Substring($currentResolved.Length).TrimStart([char[]]@([IO.Path]::DirectorySeparatorChar, [IO.Path]::AltDirectorySeparatorChar))
                $prevPath = Join-Path $prevDir $rel
                if (-not (Test-Path $prevPath)) {
                    $diffRelPaths += $rel
                } else {
                    $h1 = (Get-FileHash -Path $cf.FullName -Algorithm SHA256).Hash
                    $h2 = (Get-FileHash -Path $prevPath -Algorithm SHA256).Hash
                    if ($h1 -ne $h2) { $diffRelPaths += $rel }
                }
            }

            if ($diffRelPaths.Count -eq 0) {
                Write-Host "BuildDiff: 没有差异文件"
            } else {
                $stagingDir = Join-Path $buildDir ("diff_update_" + $versionInfo)
                if (Test-Path $stagingDir) { Remove-Item -Recurse -Force $stagingDir }
                foreach ($rel in $diffRelPaths) {
                    $src = Join-Path $distDir $rel
                    $dst = Join-Path $stagingDir $rel
                    $dstDir = Split-Path -Parent $dst
                    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
                    Copy-Item -Force $src $dst
                }

                $diffPackageName = "iaa_v$version" + "_" + "$stamp" + "_diff_update" + $(if ($has7z) { ".7z" } else { ".zip" })
                $diffOutputPath = Join-Path $repoRoot $diffPackageName

                Write-Host "Creating diff package..."
                if ($has7z) {
                    Push-Location $stagingDir
                    & 7z a -t7z -mx=9 $diffOutputPath *
                    Pop-Location
                } else {
                    if (Test-Path $diffOutputPath) { Remove-Item -Force $diffOutputPath }
                    Compress-Archive -Path "$stagingDir/*" -DestinationPath $diffOutputPath -CompressionLevel Optimal
                }
                Write-Host "Diff packaged: $diffOutputPath"
            }
        }
    }
} 