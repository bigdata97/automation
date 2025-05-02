# Step 1: Define install path
$kubectlDir = "C:\kubectl"
$kubectlExe = "$kubectlDir\kubectl.exe"

# Step 2: Create directory if not exists
New-Item -ItemType Directory -Force -Path $kubectlDir

# Step 3: Download the latest stable kubectl.exe
$latestVersion = Invoke-RestMethod -Uri "https://dl.k8s.io/release/stable.txt"
$kubectlUrl = "https://dl.k8s.io/release/$latestVersion/bin/windows/amd64/kubectl.exe"
Invoke-WebRequest -Uri $kubectlUrl -OutFile $kubectlExe

# Step 4: Add to PATH (user-level, no admin needed)
$envPath = [System.Environment]::GetEnvironmentVariable("Path", [System.EnvironmentVariableTarget]::User)
if ($envPath -notlike "*$kubectlDir*") {
    [System.Environment]::SetEnvironmentVariable("Path", "$envPath;$kubectlDir", [System.EnvironmentVariableTarget]::User)
    Write-Host "`nAdded C:\kubectl to PATH. Restart PowerShell to apply changes.`n"
} else {
    Write-Host "`nC:\kubectl is already in your PATH.`n"
}

# Step 5: Confirm
Write-Host "kubectl.exe has been downloaded to C:\kubectl"
