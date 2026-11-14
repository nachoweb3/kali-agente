# Windows launcher: preserves arguments and executes the Linux agent inside WSL2.
$ErrorActionPreference = 'Stop'
$distribution = if ($env:KALI_AGENT_WSL_DISTRO) { $env:KALI_AGENT_WSL_DISTRO } else { 'kali-linux' }
$workingDirectory = (Get-Location).Path
if ($workingDirectory.StartsWith('Microsoft.PowerShell.Core\\FileSystem::')) {
    $workingDirectory = $workingDirectory.Substring('Microsoft.PowerShell.Core\\FileSystem::'.Length)
}
$linuxBinary = if ($env:KALI_AGENT_WSL_BIN) { $env:KALI_AGENT_WSL_BIN } else { '' }
$nativeArguments = @('-d', $distribution, '--cd', $workingDirectory, '--exec', 'env', "KALI_AGENT_WSL_BIN=$linuxBinary", 'bash', '-lc', 'export PATH="$HOME/.local/bin:$PATH"; exec "${KALI_AGENT_WSL_BIN:-$HOME/.local/share/kali-agente/venv/bin/kali-agente}" "$@"', 'kali-agente') + $args
# Windows PowerShell 5.1 does not preserve native argument boundaries reliably.
# Quote for the Windows argv parser; no user argument is inserted into shell code.
if ($PSVersionTable.PSVersion.Major -lt 7) {
    $quotedArguments = @($nativeArguments | ForEach-Object {
        if ([string]$_ -match '[\s"]' -or [string]$_ -eq '') {
            '"' + ([regex]::Replace([regex]::Replace([string]$_, '(\\*)"', '$1$1\"'), '(\\+)$', '$1$1')) + '"'
        } else { [string]$_ }
    })
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = (Get-Command wsl.exe).Source
    $startInfo.UseShellExecute = $false
    $startInfo.Arguments = $quotedArguments -join ' '
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $process.WaitForExit()
    exit $process.ExitCode
}
& wsl.exe @nativeArguments
exit $LASTEXITCODE
