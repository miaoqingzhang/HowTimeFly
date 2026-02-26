# FFmpeg 安装脚本
# 以管理员身份运行 PowerShell 执行此脚本

Write-Host "=== FFmpeg 安装脚本 ===" -ForegroundColor Cyan

# 创建安装目录
$ffmpegDir = "C:\ffmpeg"
$downloadDir = "$env:TEMP\ffmpeg_install"
New-Item -Path $downloadDir -ItemType Directory -Force | Out-Null
New-Item -Path $ffmpegDir -ItemType Directory -Force | Out-Null

Write-Host "`n下载方式选择：" -ForegroundColor Yellow
Write-Host "1. 自动下载 (从镜像站)"
Write-Host "2. 手动下载提示"
$choice = Read-Host "`n请选择 (1 或 2)"

if ($choice -eq "1") {
    Write-Host "`n正在从镜像站下载 ffmpeg..." -ForegroundColor Green

    # 使用国内镜像
    $urls = @(
        "https://registry.npmmirror.com/binary.html?path=ffmpeg-builds/ffmpeg-release-essentials.zip/ffmpeg-release-essentials-7.1.zip",
        "https://ghproxy.com/https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    )

    $success = $false
    foreach ($url in $urls) {
        try {
            Write-Host "尝试: $url"
            $outputFile = "$downloadDir\ffmpeg.zip"
            Invoke-WebRequest -Uri $url -OutFile $outputFile -UseBasicParsing -TimeoutSec 60

            Write-Host "`n解压中..."
            Expand-Archive -Path $outputFile -DestinationPath $downloadDir -Force

            # 查找 bin 目录
            $binPath = (Get-ChildItem -Path $downloadDir -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1).DirectoryName
            if ($binPath) {
                Copy-Item -Path "$binPath\*" -Destination $ffmpegDir -Recurse -Force
                $success = $true
                break
            }
        }
        catch {
            Write-Host "下载失败: $_" -ForegroundColor Red
        }
    }

    if (-not $success) {
        Write-Host "`n自动下载失败，请使用手动方式" -ForegroundColor Red
        $choice = "2"
    }
}

if ($choice -eq "2") {
    Write-Host "`n=== 手动安装 ffmpeg ===" -ForegroundColor Yellow
    Write-Host "1. 访问以下任一下载链接："
    Write-Host "   - https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
    Write-Host "   - https://github.com/BtbN/FFmpeg-Builds/releases/latest"
    Write-Host "`n2. 下载 ffmpeg-release-essentials.zip 或类似的 Windows 版本"
    Write-Host "3. 解压到 $ffmpegDir"
    Write-Host "`n4. 确保目录结构是: $ffmpegDir\bin\ffmpeg.exe"
    Write-Host "`n5. 按任意键继续添加到 PATH..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# 检查 ffmpeg 是否存在
$ffmpegExe = "$ffmpegDir\bin\ffmpeg.exe"
if (Test-Path $ffmpegExe) {
    Write-Host "`nffmpeg.exe 找到: $ffmpegExe" -ForegroundColor Green

    # 添加到系统 PATH
    $binPath = "$ffmpegDir\bin"
    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment"
    $currentPath = (Get-ItemProperty -Path $regPath -Name Path).Path

    if ($currentPath -notlike "*$binPath*") {
        Write-Host "`n添加到系统 PATH..." -ForegroundColor Yellow
        $newPath = "$currentPath;$binPath"
        Set-ItemProperty -Path $regPath -Name Path -Value $newPath
        Write-Host "已添加！需要重启终端或重新登录才能生效。" -ForegroundColor Green

        # 添加到当前会话
        $env:Path += ";$binPath"
    } else {
        Write-Host "已在 PATH 中" -ForegroundColor Green
    }

    Write-Host "`n=== 测试 ffmpeg ===" -ForegroundColor Cyan
    & $ffmpegExe -version
    Write-Host "`n安装成功！" -ForegroundColor Green
} else {
    Write-Host "`n未找到 ffmpeg.exe，请手动安装后重试" -ForegroundColor Red
    Write-Host "期望位置: $ffmpegExe"
}

Write-Host "`n按任意键退出..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
