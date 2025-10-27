# Script de Execução Rápida - Conversão de Dados Reais
# ======================================================
# Este script PowerShell facilita a execução da conversão de dados reais
# para o formato padronizado do RecifeSafe.

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host "🌊 RecifeSafe - Conversão de Dados Reais" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está no diretório correto
if (-not (Test-Path "src/data/convert_real_to_synthetic_format.py")) {
    Write-Host "❌ Erro: Execute este script a partir da raiz do projeto RecifeSafe" -ForegroundColor Red
    Write-Host "   Diretório atual: $(Get-Location)" -ForegroundColor Yellow
    Write-Host "   Diretório esperado: D:\PENTES\PENTES\RecifeSafe\" -ForegroundColor Yellow
    exit 1
}

# Definir caminhos
$marePath = "data\processed\2024.csv"
$chuvaPath = "data\processed\Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv"
$outputPath = "data\processed\real_data_converted.csv"

# Verificar se arquivos de entrada existem
Write-Host "🔍 Verificando arquivos de entrada..." -ForegroundColor Yellow
Write-Host ""

$filesOk = $true

if (Test-Path $marePath) {
    Write-Host "   ✅ Arquivo de marés encontrado: $marePath" -ForegroundColor Green
} else {
    Write-Host "   ❌ Arquivo de marés NÃO encontrado: $marePath" -ForegroundColor Red
    $filesOk = $false
}

if (Test-Path $chuvaPath) {
    Write-Host "   ✅ Arquivo de chuva encontrado: $chuvaPath" -ForegroundColor Green
} else {
    Write-Host "   ❌ Arquivo de chuva NÃO encontrado: $chuvaPath" -ForegroundColor Red
    $filesOk = $false
}

Write-Host ""

if (-not $filesOk) {
    Write-Host "❌ Arquivos de entrada ausentes. Verifique os caminhos." -ForegroundColor Red
    Write-Host ""
    Write-Host "📁 Estrutura esperada:" -ForegroundColor Yellow
    Write-Host "   data/" -ForegroundColor Gray
    Write-Host "   └── processed/" -ForegroundColor Gray
    Write-Host "       ├── 2024.csv" -ForegroundColor Gray
    Write-Host "       └── Dados pluviométricos da APAC - Região metropolitana de Recife - 2024.csv" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

# Perguntar ao usuário se quer usar seed personalizado
Write-Host "🎲 Seed para reprodutibilidade (padrão: 42)" -ForegroundColor Yellow
$seedInput = Read-Host "   Digite um número ou pressione Enter para usar o padrão"
$seed = if ($seedInput -eq "") { 42 } else { [int]$seedInput }
Write-Host ""

# Executar conversão
Write-Host "🚀 Iniciando conversão..." -ForegroundColor Cyan
Write-Host "   Entrada - Marés: $marePath" -ForegroundColor Gray
Write-Host "   Entrada - Chuva: $chuvaPath" -ForegroundColor Gray
Write-Host "   Saída: $outputPath" -ForegroundColor Gray
Write-Host "   Seed: $seed" -ForegroundColor Gray
Write-Host ""

# Executar o script Python
& python src\data\convert_real_to_synthetic_format.py `
    --mare $marePath `
    --chuva $chuvaPath `
    --output $outputPath `
    --seed $seed

# Verificar se conversão foi bem-sucedida
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host "✅ Conversão concluída com sucesso!" -ForegroundColor Green
    Write-Host "========================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Próximos passos:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "1️⃣ Visualizar dados convertidos:" -ForegroundColor Yellow
    Write-Host "   python -c `"import pandas as pd; df=pd.read_csv('$outputPath'); print(df.head(20)); print('\n', df.describe())`"" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2️⃣ Substituir dados sintéticos (BACKUP RECOMENDADO):" -ForegroundColor Yellow
    Write-Host "   Copy-Item data\processed\simulated_daily.csv data\processed\simulated_daily_backup.csv" -ForegroundColor Gray
    Write-Host "   Copy-Item $outputPath data\processed\simulated_daily.csv" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3️⃣ Treinar modelos com dados reais:" -ForegroundColor Yellow
    Write-Host "   python src\models\train_models.py" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4️⃣ Executar dashboard com dados reais:" -ForegroundColor Yellow
    Write-Host "   streamlit run src\dashboard\app.py" -ForegroundColor Gray
    Write-Host ""
    
    # Perguntar se quer substituir dados sintéticos
    Write-Host "========================================================================" -ForegroundColor Cyan
    $replace = Read-Host "Deseja substituir os dados sintéticos pelos dados reais agora? (s/N)"
    
    if ($replace -eq "s" -or $replace -eq "S") {
        Write-Host ""
        Write-Host "📦 Fazendo backup dos dados sintéticos..." -ForegroundColor Yellow
        
        if (Test-Path "data\processed\simulated_daily.csv") {
            Copy-Item "data\processed\simulated_daily.csv" "data\processed\simulated_daily_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss').csv"
            Write-Host "   ✅ Backup criado" -ForegroundColor Green
        }
        
        Write-Host ""
        Write-Host "🔄 Substituindo dados..." -ForegroundColor Yellow
        Copy-Item $outputPath "data\processed\simulated_daily.csv"
        Write-Host "   ✅ Dados substituídos" -ForegroundColor Green
        Write-Host ""
        
        Write-Host "🤖 Deseja treinar os modelos agora? (s/N)" -ForegroundColor Cyan
        $train = Read-Host
        
        if ($train -eq "s" -or $train -eq "S") {
            Write-Host ""
            Write-Host "🚀 Treinando modelos..." -ForegroundColor Cyan
            & python src\models\train_models.py
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "✅ Modelos treinados com sucesso!" -ForegroundColor Green
                Write-Host ""
                Write-Host "🌐 Deseja iniciar o dashboard agora? (s/N)" -ForegroundColor Cyan
                $dashboard = Read-Host
                
                if ($dashboard -eq "s" -or $dashboard -eq "S") {
                    Write-Host ""
                    Write-Host "🌐 Iniciando dashboard..." -ForegroundColor Cyan
                    Write-Host "   Acesse: http://localhost:8501" -ForegroundColor Yellow
                    Write-Host ""
                    streamlit run src\dashboard\app.py
                }
            }
        }
    }
    
} else {
    Write-Host ""
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host "❌ Erro durante a conversão" -ForegroundColor Red
    Write-Host "========================================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "📝 Verifique os erros acima e consulte a documentação:" -ForegroundColor Yellow
    Write-Host "   docs\CONVERSAO_DADOS_REAIS.md" -ForegroundColor Gray
    Write-Host ""
    exit 1
}
