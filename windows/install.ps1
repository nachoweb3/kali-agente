$ErrorActionPreference = 'Stop'
function Invoke-Wsl {
    param([string[]]$WslArguments, [switch]$Capture)
    $quoted = @($WslArguments | ForEach-Object {
        if ([string]$_ -match '[\s"]' -or [string]$_ -eq '') {
            '"' + ([regex]::Replace([regex]::Replace([string]$_, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')) + '"'
        } else { [string]$_ }
    })
    $info = New-Object System.Diagnostics.ProcessStartInfo
    $info.FileName = (Get-Command wsl.exe).Source
    $info.UseShellExecute = $false
    $info.Arguments = $quoted -join ' '
    $info.RedirectStandardOutput = [bool]$Capture
    $process = [System.Diagnostics.Process]::Start($info)
    if ($Capture) { $outputText = $process.StandardOutput.ReadToEnd() }
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "WSL fallo con codigo $($process.ExitCode)" }
    if ($Capture) { return $outputText.Trim() }
}
$distribution = if ($env:KALI_AGENT_WSL_DISTRO) { $env:KALI_AGENT_WSL_DISTRO } else { 'kali-linux' }
$sourceDirectory = Split-Path -Parent $PSScriptRoot
Invoke-Wsl -WslArguments @('-d', $distribution, '--exec', 'true')
$linuxSource = Invoke-Wsl -WslArguments @('-d', $distribution, '--exec', 'wslpath', '-a', $sourceDirectory) -Capture
Invoke-Wsl -WslArguments @('-d', $distribution, '--exec', 'bash', "$linuxSource/scripts/install.sh")
$destination = Join-Path $env:LOCALAPPDATA 'Programs\KaliAgente'
New-Item -ItemType Directory -Force -Path $destination | Out-Null
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'kali-agente.ps1') -Destination $destination -Force
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'kali-agente.cmd') -Destination $destination -Force
$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($null -eq $userPath) { $userPath = '' }
if (($userPath -split ';') -notcontains $destination) {
    [Environment]::SetEnvironmentVariable('Path', (($userPath.TrimEnd(';') + ';' + $destination).TrimStart(';')), 'User')
}
$env:Path = "$env:Path;$destination"
Write-Host "Instalado para CMD y PowerShell: $destination"
Write-Host 'Abre una terminal nueva y ejecuta: kali-agente --help'
