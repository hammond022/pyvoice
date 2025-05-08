
if (!([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) { Start-Process powershell.exe "-NoProfile -ExecutionPolicy Bypass -File `"$PSCommandPath`"" -Verb RunAs; exit }
# Create Maven directory
$mavenPath = "C:\Program Files\Apache\maven"
if (-not (Test-Path $mavenPath)) {
    New-Item -ItemType Directory -Path $mavenPath -Force
}

# Download Maven
$mavenUrl = "https://dlcdn.apache.org/maven/maven-3/3.9.6/binaries/apache-maven-3.9.6-bin.zip"
$zipFile = "$env:TEMP\maven.zip"
Invoke-WebRequest -Uri $mavenUrl -OutFile $zipFile

# Extract Maven
Expand-Archive -Path $zipFile -DestinationPath "C:\Program Files\Apache" -Force
Move-Item "C:\Program Files\Apache\apache-maven-3.9.6\*" $mavenPath -Force

# Set environment variables
$env:M2_HOME = $mavenPath
[Environment]::SetEnvironmentVariable("M2_HOME", $mavenPath, "Machine")

# Add to PATH
$path = [Environment]::GetEnvironmentVariable("Path", "Machine")
if ($path -notlike "*$mavenPath\bin*") {
    [Environment]::SetEnvironmentVariable("Path", "$path;$mavenPath\bin", "Machine")
}

Write-Host "Maven has been installed. Please restart your terminal/IDE to use 'mvn' commands."
