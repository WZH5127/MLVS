# 获取脚本所在目录的上级目录
$projectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# 检查 Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "错误：未安装 Python，请先安装！"
    exit 1
}

# 切换到项目根目录并运行
Set-Location $projectRoot
python sp.py