#Requires -Version 5.1
<#
.SYNOPSIS
  将本机「世界模型」资料目录以 Directory Junction 挂到 external/world_model。

.DESCRIPTION
  - 不复制文件，不创建 Git Submodule
  - 挂载点已被 .gitignore 忽略，不会进入本仓库
  - 默认：在仓库父目录下查找含 README.md 且目录名匹配的「世界模型」文件夹

.PARAMETER SourcePath
  世界模型资料目录的绝对路径。省略时自动在仓库同级目录中解析。
#>
param(
    [string]$SourcePath = ""
)

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$LinkPath = Join-Path $RepoRoot "external\world_model"
$ExternalDir = Join-Path $RepoRoot "external"
$ParentDir = Split-Path $RepoRoot -Parent

function Find-WorldModelSource {
    param([string]$Parent)
    # 优先：目录名以「世界」开头且含 README（避免脚本文件编码破坏中文默认值）
    $candidates = Get-ChildItem -LiteralPath $Parent -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -like "*模型*" -or $_.Name -match "world" }
    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath (Join-Path $c.FullName "README.md")) {
            # 进一步确认是资料库（含 docs/ 与 papers/）
            if ((Test-Path -LiteralPath (Join-Path $c.FullName "docs")) -and
                (Test-Path -LiteralPath (Join-Path $c.FullName "papers"))) {
                return $c.FullName
            }
        }
    }
    return $null
}

if ([string]::IsNullOrWhiteSpace($SourcePath)) {
    $SourcePath = Find-WorldModelSource -Parent $ParentDir
    if (-not $SourcePath) {
        Write-Error @"
未能在父目录自动找到世界模型资料库: $ParentDir
请显式指定，例如:
  .\scripts\link_external_world_model.ps1 -SourcePath 'D:\project\世界模型'
"@
    }
}

if (-not (Test-Path -LiteralPath $SourcePath)) {
    Write-Error "源路径不存在: $SourcePath"
}

$SourcePath = (Resolve-Path -LiteralPath $SourcePath).Path

if (-not (Test-Path -LiteralPath $ExternalDir)) {
    New-Item -ItemType Directory -Path $ExternalDir | Out-Null
}

if (Test-Path -LiteralPath $LinkPath) {
    $item = Get-Item -LiteralPath $LinkPath -Force
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
        Write-Host "移除已有挂载点: $LinkPath"
        cmd /c "rmdir `"$LinkPath`""
        if ($LASTEXITCODE -ne 0) {
            Write-Error "无法移除已有挂载点: $LinkPath"
        }
    }
    else {
        Write-Error "路径已存在且不是 junction/symlink，请手动处理: $LinkPath"
    }
}

Write-Host "创建 Directory Junction:"
Write-Host "  $LinkPath"
Write-Host "  -> $SourcePath"

cmd /c "mklink /J `"$LinkPath`" `"$SourcePath`""
if ($LASTEXITCODE -ne 0) {
    Write-Error "mklink /J 失败（exit=$LASTEXITCODE）"
}

$readme = Join-Path $LinkPath "README.md"
if (-not (Test-Path -LiteralPath $readme)) {
    Write-Warning "挂载已创建，但未找到 README.md，请确认源目录是否正确。"
}
else {
    Write-Host "OK: 已挂载，可读 $readme"
}

Get-Item -LiteralPath $LinkPath | Format-List FullName, LinkType, Target
