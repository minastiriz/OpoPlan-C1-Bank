param(
    [Parameter(Mandatory = $true)][string]$PackPath,
    [Parameter(Mandatory = $true)][string]$CertificateThumbprint
)

$resolvedPack = (Resolve-Path -LiteralPath $PackPath).Path
$certificate = Get-Item -LiteralPath "Cert:\CurrentUser\My\$CertificateThumbprint"
$privateKey = [System.Security.Cryptography.X509Certificates.ECDsaCertificateExtensions]::GetECDsaPrivateKey($certificate)
if ($null -eq $privateKey) { throw "El certificado no contiene una clave ECDSA privada." }

$bytes = [System.IO.File]::ReadAllBytes($resolvedPack)
$hash = [System.Security.Cryptography.SHA256]::HashData($bytes)
$signature = $privateKey.SignData(
    $bytes,
    [System.Security.Cryptography.HashAlgorithmName]::SHA256,
    [System.Security.Cryptography.DSASignatureFormat]::Rfc3279DerSequence
)

[PSCustomObject]@{
    sha256 = [Convert]::ToHexString($hash).ToLowerInvariant()
    signature = [Convert]::ToBase64String($signature)
} | ConvertTo-Json -Compress
