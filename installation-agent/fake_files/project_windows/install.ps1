# PowerShell Setup script
Write-Output "Configuring Windows installation..."
$env:DB_PORT = "1433"
New-Item -ItemType Directory -Path "C:\Program Files\WindowsDevOps"
Copy-Item -Path ".\config.ini" -Destination "C:\Program Files\WindowsDevOps\config.ini"
& .\setup.exe /S
