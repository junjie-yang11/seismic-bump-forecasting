param(
    [ValidateSet('overall','ranking','information')][string]$ReportDirectory = 'overall',
    [ValidateSet('integrated_research_report','within_grade_ranking_pilot','monitoring_information_increment','decision_comparison_supplement')][string]$Stem = 'integrated_research_report'
)
$ErrorActionPreference = 'Stop'
$reportRoot = Join-Path (Split-Path $PSScriptRoot -Parent) ('reports/' + $ReportDirectory)
$temporaryPdf = Join-Path ([System.IO.Path]::GetTempPath()) ('seismic_overall.' + [guid]::NewGuid().ToString('N') + '.pdf')
$word = $null
$document = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
    $word.DisplayAlerts = 0
    $document = $word.Documents.Open((Join-Path $reportRoot ($Stem + '.docx')), $false, $true)
    # Microsoft documents OptimizeForImageQuality as parameter 15 of this API:
    # https://learn.microsoft.com/en-us/office/vba/api/word.document.exportasfixedformat2
    # Request print output, omit document properties, keep heading bookmarks and
    # accessibility tags, and request original image quality. Some Word builds
    # still downsample rasters; verify the exported PDF itself and prefer the
    # vector alternatives embedded by the writer for research figures.
    $document.ExportAsFixedFormat2($temporaryPdf, 17, $false, 0, 0, 1, 1, 0, $false, $true, 1, $true, $true, $false, $true)
    Copy-Item -LiteralPath $temporaryPdf -Destination (Join-Path $reportRoot ($Stem + '.pdf')) -Force
} finally {
    if ($document) { $document.Close(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($document) | Out-Null }
    if ($word) { $word.Quit(0); [Runtime.InteropServices.Marshal]::ReleaseComObject($word) | Out-Null }
    if (Test-Path -LiteralPath $temporaryPdf) { Remove-Item -LiteralPath $temporaryPdf }
}
