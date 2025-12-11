# Helper function to load .env.local into PowerShell environment
# Usage: . .\scripts\load_env_helper.ps1; Load-EnvLocal

function Load-EnvLocal {
    param(
        [string]$EnvFilePath = ".env.local"
    )
    
    $fullPath = Join-Path (Get-Location) $EnvFilePath
    
    if (-not (Test-Path $fullPath)) {
        Write-Warning ".env.local not found at: $fullPath"
        return $false
    }
    
    $loaded = 0
    Get-Content $fullPath | ForEach-Object {
        $line = $_.Trim()
        # Skip comments and empty lines
        if ($line -and -not $line.StartsWith('#')) {
            if ($line -match '^\s*([^#][^=]+)=(.*)$') {
                $key = $matches[1].Trim()
                $value = $matches[2].Trim()
                
                # Remove quotes if present
                if ($value -match '^["''](.*)["'']$') {
                    $value = $matches[1]
                }
                
                # Set environment variable
                [Environment]::SetEnvironmentVariable($key, $value, "Process")
                $loaded++
            }
        }
    }
    
    Write-Host "✅ Loaded $loaded environment variables from .env.local" -ForegroundColor Green
    return $true
}

# Export the function
Export-ModuleMember -Function Load-EnvLocal

