<#
    Buy Box Check Automation - Windows Task Scheduler template.

    THIS SCRIPT DOES NOT ACTIVATE ANYTHING BY DEFAULT.
    -RunTime is mandatory and has no default, because the run hour is an unapproved
    business decision. Without -Confirm the script only prints what it would register.

    Register (after approval):
        .\scheduler.ps1 -RunTime "09:30" -Confirm

    Inspect / remove:
        .\scheduler.ps1 -Show
        .\scheduler.ps1 -Remove -Confirm

    House conventions followed (matching the other 50 tasks on this machine):
      * pythonw.exe + automation\run.py, WorkingDirectory = automation
      * Interactive / Limited principal  (NOT S4U, NOT Highest)
      * MultipleInstances = IgnoreNew    (overlapping-run prevention)
      * StartWhenAvailable = true        (safe resume after the machine was off)

    Upstream dependency: the PH spine is refreshed by ph_dashboard's
    `overall_asin_daily` at 35 7 * * * Asia/Colombo. Pick a run time AFTER that
    completes, or the run reads yesterday's ASIN list.
#>
[CmdletBinding()]
param(
    [string]$RunTime,                       # "HH:mm" local - REQUIRED to register
    [string]$TaskName = 'BBOX_Daily_Buy_Box_Check',
    [switch]$Confirm,
    [switch]$Show,
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'
$AutomationDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RunPy         = Join-Path $AutomationDir 'run.py'
$PythonW       = 'C:\Program Files\Python313\pythonw.exe'

function Show-Task {
    $t = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if (-not $t) { Write-Host "Task '$TaskName' is not registered."; return }
    Write-Host "Task '$TaskName':" -ForegroundColor Cyan
    $t.Actions    | Select-Object Execute, Arguments, WorkingDirectory | Format-List
    $t.Triggers   | Select-Object StartBoundary, DaysInterval, Enabled | Format-List
    $t.Principal  | Select-Object UserId, LogonType, RunLevel          | Format-List
    $t.Settings   | Select-Object MultipleInstances, ExecutionTimeLimit, StartWhenAvailable | Format-List
    Get-ScheduledTaskInfo -TaskName $TaskName |
        Select-Object LastRunTime, LastTaskResult, NextRunTime | Format-List
}

if ($Show)   { Show-Task; exit 0 }

if ($Remove) {
    if (-not $Confirm) { Write-Host "Would unregister '$TaskName'. Re-run with -Confirm."; exit 0 }
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Host "Unregistered '$TaskName'."
    exit 0
}

# --- preconditions -----------------------------------------------------------
if (-not (Test-Path $RunPy))   { throw "run.py not found at $RunPy" }
if (-not (Test-Path $PythonW)) { throw "pythonw.exe not found at $PythonW" }

if (-not $RunTime) {
    Write-Host ""
    Write-Host "BLOCKED: -RunTime is required and has no default." -ForegroundColor Yellow
    Write-Host "The daily run hour and timezone are not yet approved, so this script will"
    Write-Host "not pick one for you. Supply an approved time, e.g. -RunTime '09:30'."
    Write-Host ""
    Write-Host "Note: the PH spine refreshes at 07:35 Asia/Colombo (overall_asin_daily),"
    Write-Host "so an approved time should fall after that."
    exit 2
}

try { [datetime]::ParseExact($RunTime, 'HH:mm', $null) | Out-Null }
catch { throw "RunTime must be HH:mm (24-hour), got '$RunTime'" }

$action = New-ScheduledTaskAction -Execute $PythonW `
            -Argument ('"{0}"' -f $RunPy) -WorkingDirectory $AutomationDir
$trigger = New-ScheduledTaskTrigger -Daily -At $RunTime
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME `
               -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew `
              -StartWhenAvailable -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
              -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 10)

if (-not $Confirm) {
    Write-Host ""
    Write-Host "DRY RUN - nothing registered. Would create:" -ForegroundColor Yellow
    Write-Host "  Task        : $TaskName"
    Write-Host "  Execute     : $PythonW"
    Write-Host "  Arguments   : `"$RunPy`""
    Write-Host "  WorkingDir  : $AutomationDir"
    Write-Host "  Trigger     : daily at $RunTime (machine local time)"
    Write-Host "  Principal   : $env:USERNAME / Interactive / Limited"
    Write-Host "  Overlap     : IgnoreNew"
    Write-Host "  Time limit  : 2 hours, restart up to 2x after 10 min"
    Write-Host ""
    Write-Host "Re-run with -Confirm to register. Confirm the run time with the owner first."
    exit 0
}

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger `
    -Principal $principal -Settings $settings `
    -Description 'Buy Box Check Automation (Tharsi) - daily full check. See automation/README.md.' `
    -Force | Out-Null

Write-Host "Registered '$TaskName' - daily at $RunTime." -ForegroundColor Green
Write-Host "Record the approved time and timezone in automation/config.local.json"
Write-Host "and set the daily_schedule_approved gate."
Show-Task
