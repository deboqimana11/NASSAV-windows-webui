$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot
python queue_runner.py
exit $LASTEXITCODE
