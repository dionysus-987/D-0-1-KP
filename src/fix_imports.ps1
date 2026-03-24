# =========================
# 1. –ﬁ∏¥ instance_service.py
# =========================
$filePath = "app\services\instance_service.py"
if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw
    $content = $content -replace '(?m)^from parser_utils import', 'import sys; from pathlib import Path; sys.path.insert(0, str(Path(__file__).resolve().parents[2])); from parser_utils import'
    Set-Content $filePath $content -Encoding UTF8
    Write-Host "? Fixed instance_service.py" -ForegroundColor Green
}

# =========================
# 2. –ﬁ∏¥ experiment_service.py  
# =========================
$filePath = "app\services\experiment_service.py"
if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw
    $importFix = @"
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"@
    $content = $content -replace '(?m)^from app\.services\.instance_service import', 'from .instance_service import'
    $lines = $content -split "`n"
    $newLines = @()
    $added = $false
    foreach ($line in $lines) {
        if (-not $added -and $line -match '^from __future__') {
            $newLines += $line
            $newLines += $importFix
            $added = $true
        } else {
            $newLines += $line
        }
    }
    Set-Content $filePath ($newLines -join "`n") -Encoding UTF8
    Write-Host "? Fixed experiment_service.py" -ForegroundColor Green
}

# =========================
# 3. –ﬁ∏¥ export_service.py
# =========================
$filePath = "app\services\export_service.py"
if (Test-Path $filePath) {
    $content = Get-Content $filePath -Raw
    $importFix = @"
import sys
from pathlib import Path
_root = Path(__file__).resolve().parents[2]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

"@
    $content = $content -replace '(?m)^from services\.experiment_service import', 'from .experiment_service import'
    $lines = $content -split "`n"
    $newLines = @()
    $added = $false
    foreach ($line in $lines) {
        if (-not $added -and $line -match '^from __future__') {
            $newLines += $line
            $newLines += $importFix
            $added = $true
        } else {
            $newLines += $line
        }
    }
    Set-Content $filePath ($newLines -join "`n") -Encoding UTF8
    Write-Host "? Fixed export_service.py" -ForegroundColor Green
}

# =========================
# 4. «Â¿Ìª∫¥Ê
# =========================
Get-ChildItem -Recurse -Include __pycache__ | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -Include "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "? ª∫¥Ê“—«Â¿Ì" -ForegroundColor Green
