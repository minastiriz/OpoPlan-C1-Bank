param(
    [Parameter(Mandatory = $true)]
    [string]$DataPath,

    [Parameter(Mandatory = $true)]
    [string]$SignatureBase64,

    [Parameter(Mandatory = $true)]
    [string]$PublicKeyPath
)

$ErrorActionPreference = 'Stop'

$pem = Get-Content -LiteralPath $PublicKeyPath -Raw
$publicKeyBase64 = $pem `
    -replace '-----BEGIN PUBLIC KEY-----', '' `
    -replace '-----END PUBLIC KEY-----', '' `
    -replace '\s', ''

$publicKeyBytes = [Convert]::FromBase64String($publicKeyBase64)
$derSignature = [Convert]::FromBase64String($SignatureBase64)
$dataBytes = [IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $DataPath))

if ($publicKeyBytes.Length -lt 65 -or $publicKeyBytes[$publicKeyBytes.Length - 65] -ne 4) {
    throw 'La clave pública P-256 no tiene un formato compatible.'
}

$pointOffset = $publicKeyBytes.Length - 64
$publicBlob = New-Object byte[] 72
[byte[]]$header = 0x45, 0x43, 0x53, 0x31, 0x20, 0x00, 0x00, 0x00
[Array]::Copy($header, 0, $publicBlob, 0, $header.Length)
[Array]::Copy($publicKeyBytes, $pointOffset, $publicBlob, 8, 64)

if ($derSignature.Length -lt 8 -or $derSignature[0] -ne 0x30 -or $derSignature[2] -ne 0x02) {
    throw 'La firma DER no tiene un formato compatible.'
}
$rLength = [int]$derSignature[3]
$rOffset = 4
$sTagOffset = $rOffset + $rLength
if ($sTagOffset + 2 -gt $derSignature.Length -or $derSignature[$sTagOffset] -ne 0x02) {
    throw 'La firma DER no contiene el valor S esperado.'
}
$sLength = [int]$derSignature[$sTagOffset + 1]
$sOffset = $sTagOffset + 2

function Copy-NormalizedInteger([byte[]]$Source, [int]$Offset, [int]$Length, [byte[]]$Target, [int]$TargetOffset) {
    while ($Length -gt 32 -and $Source[$Offset] -eq 0) {
        $Offset++
        $Length--
    }
    if ($Length -gt 32) {
        throw 'La firma contiene un entero mayor de 256 bits.'
    }
    [Array]::Copy($Source, $Offset, $Target, $TargetOffset + 32 - $Length, $Length)
}

$signatureBytes = New-Object byte[] 64
Copy-NormalizedInteger $derSignature $rOffset $rLength $signatureBytes 0
Copy-NormalizedInteger $derSignature $sOffset $sLength $signatureBytes 32

$key = [Security.Cryptography.CngKey]::Import(
    $publicBlob,
    [Security.Cryptography.CngKeyBlobFormat]::EccPublicBlob
)
$ecdsa = New-Object Security.Cryptography.ECDsaCng($key)

try {
    $valid = $ecdsa.VerifyData(
        $dataBytes,
        $signatureBytes,
        [Security.Cryptography.HashAlgorithmName]::SHA256
    )
    if (-not $valid) {
        throw 'La firma ECDSA no es válida.'
    }
} finally {
    $ecdsa.Dispose()
    $key.Dispose()
}
