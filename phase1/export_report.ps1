$ErrorActionPreference = 'Stop'
$reportRoot = Join-Path (Split-Path $PSScriptRoot -Parent) 'reports/phase1'
$word = $null
$document = $null
$temporaryPdf = Join-Path ([System.IO.Path]::GetTempPath()) ('seismic_report.' + [guid]::NewGuid().ToString('N') + '.pdf')
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Join-Path $reportRoot 'technical_report.docx'), $false, $true)
    # Exclude document properties from the externally shared PDF.
    # Export to a fresh path before replacing a PDF that may be open in a viewer.
    $document.ExportAsFixedFormat($temporaryPdf, 17, $false, 0, 0, 1, 1, 0, $false)
    Copy-Item -LiteralPath $temporaryPdf -Destination (Join-Path $reportRoot 'technical_report.pdf') -Force
} finally {
    if ($document) { $document.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null }
    if ($word) { $word.Quit(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
    if (Test-Path -LiteralPath $temporaryPdf) { Remove-Item -LiteralPath $temporaryPdf }
}
