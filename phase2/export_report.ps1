$ErrorActionPreference = 'Stop'
$reportRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'results/phase2/report'
$temporaryPdf = Join-Path ([System.IO.Path]::GetTempPath()) ('seismic_phase2.' + [guid]::NewGuid().ToString('N') + '.pdf')
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Join-Path $reportRoot 'phase2_threshold_transfer_report.docx'), $false, $true)
    $document.ExportAsFixedFormat($temporaryPdf, 17, $false, 0, 0, 1, 1, 0, $false)
    Copy-Item -LiteralPath $temporaryPdf -Destination (Join-Path $reportRoot 'phase2_threshold_transfer_report.pdf') -Force
} finally {
    if ($document) { $document.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null }
    if ($word) { $word.Quit(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
    if (Test-Path -LiteralPath $temporaryPdf) { Remove-Item -LiteralPath $temporaryPdf }
}
