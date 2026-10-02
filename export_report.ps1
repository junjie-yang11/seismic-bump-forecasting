$ErrorActionPreference = 'Stop'
$reportRoot = Join-Path $PSScriptRoot 'report'
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Join-Path $reportRoot 'technical_report.docx'), $false, $true)
    # Exclude document properties from the externally shared PDF.
    $document.ExportAsFixedFormat((Join-Path $reportRoot 'technical_report.pdf'), 17, $false, 0, 0, 1, 1, 0, $false)
} finally {
    if ($document) { $document.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null }
    if ($word) { $word.Quit(); [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
}
