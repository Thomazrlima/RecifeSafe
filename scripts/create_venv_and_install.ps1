Param(
    [string]$VenvName = ".venv"
)

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot

Write-Host "Usando diretório: $repoRoot"
if (-not (Test-Path $VenvName)) {
    Write-Host "Criando virtualenv em $VenvName..."
    python -m venv $VenvName
} else {
    Write-Host "Virtualenv já existe em $VenvName"
}

$pipPath = Join-Path $VenvName "Scripts\pip.exe"
if (Test-Path $pipPath) {
    Write-Host "Instalando/upgrading pip e dependências a partir de requirements.txt..."
    & $pipPath install --upgrade pip
    if (Test-Path (Join-Path $repoRoot "requirements.txt")) {
        & $pipPath install -r (Join-Path $repoRoot "requirements.txt")
        Write-Host "Dependências instaladas."
    } else {
        Write-Host "requirements.txt não encontrado em $repoRoot"
    }
    Write-Host "Para ativar o ambiente (PowerShell):"
    Write-Host "  .\$VenvName\Scripts\Activate.ps1"
} else {
    Write-Host "pip não encontrado em $VenvName. Ative o venv manualmente e instale dependências: pip install -r requirements.txt"
}
