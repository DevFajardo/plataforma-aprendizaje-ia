<#
.SYNOPSIS
  Inicia la plataforma para una demostración en la red local (LAN): otros equipos y celulares
  conectados al mismo Wi-Fi/Ethernet pueden entrar, incluida la clase en vivo con QR.

.DESCRIPTION
  1. Detecta la IPv4 de la red Wi-Fi/Ethernet activa (la del adaptador con puerta de enlace).
  2. Arranca el backend en 0.0.0.0:8000 con FRONTEND_URL = localhost + IP.
  3. Compila (si hace falta) y arranca el frontend en 0.0.0.0:3000 con
     NEXT_PUBLIC_API_URL=http://IP:8000 y NEXT_PUBLIC_URL_PUBLICA=http://IP:3000 (para que el QR use la IP).
  4. Muestra las URLs para el público.

  Uso:   .\iniciar_demo.ps1            (modo producción: build + start, más rápido)
         .\iniciar_demo.ps1 -Dev       (next dev, sin compilar)
         .\iniciar_demo.ps1 -Ip 192.168.1.50   (forzar una IP)

  FIREWALL DE WINDOWS: la primera vez, Windows bloquea las conexiones entrantes. Abre los puertos 3000 y 8000
  ejecutando UNA VEZ, en una PowerShell como administrador (este script NO lo hace por ti):

      # New-NetFirewallRule -DisplayName "Aprendizaje Activo (demo LAN)" -Direction Inbound `
      #     -Protocol TCP -LocalPort 3000,8000 -Action Allow -Profile Private

  Con -Profile Private solo se permite en redes marcadas como «Privada». Para quitarla después:
      # Remove-NetFirewallRule -DisplayName "Aprendizaje Activo (demo LAN)"

  Nota: los servidores de desarrollo habituales (8000/3000) deben estar detenidos antes de ejecutar este script.
#>
param(
    [switch]$Dev,
    [string]$Ip = ""
)

$ErrorActionPreference = "Stop"
$raiz = Split-Path -Parent $MyInvocation.MyCommand.Path

# --- 1. IP local de la red activa (adaptador con puerta de enlace IPv4 predeterminada) ---
if (-not $Ip) {
    $config = Get-NetIPConfiguration | Where-Object { $_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq "Up" } | Select-Object -First 1
    if ($config) { $Ip = ($config.IPv4Address | Select-Object -First 1).IPAddress }
}
if (-not $Ip) {
    Write-Host "No se detectó una red activa. Conéctate a un Wi-Fi/Ethernet o usa -Ip <dirección>." -ForegroundColor Red
    exit 1
}

$urlWeb = "http://${Ip}:3000"
$urlApi = "http://${Ip}:8000"

foreach ($puerto in 3000, 8000) {
    if (Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue) {
        Write-Host "El puerto $puerto ya está en uso. Detén ese servidor primero." -ForegroundColor Red
        exit 1
    }
}

# --- 2. Backend ---
Write-Host "Iniciando backend en 0.0.0.0:8000 ..." -ForegroundColor Cyan
$env:FRONTEND_URL = "http://localhost:3000,http://127.0.0.1:3000,$urlWeb"
$backend = Start-Process -FilePath "$raiz\backend\.venv\Scripts\python.exe" `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory "$raiz\backend" -PassThru -WindowStyle Minimized

# --- 3. Frontend ---
$env:NEXT_PUBLIC_API_URL = $urlApi
$env:NEXT_PUBLIC_URL_PUBLICA = $urlWeb
Push-Location "$raiz\frontend"
try {
    if ($Dev) {
        Write-Host "Iniciando frontend (next dev) en 0.0.0.0:3000 ..." -ForegroundColor Cyan
        $frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npx next dev -H 0.0.0.0 -p 3000" -PassThru -WindowStyle Minimized
    } else {
        Write-Host "Compilando el frontend (la IP se incrusta al compilar) ..." -ForegroundColor Cyan
        & cmd.exe /c "npx next build"
        if ($LASTEXITCODE -ne 0) { throw "Falló la compilación del frontend." }
        $frontend = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "npx next start -H 0.0.0.0 -p 3000" -PassThru -WindowStyle Minimized
    }
} finally {
    Pop-Location
}

Write-Host ""
Write-Host "================ DEMO EN RED LOCAL ================" -ForegroundColor Green
Write-Host "  Para el público (mismo Wi-Fi):  $urlWeb"
Write-Host "  Unirse a clase en vivo:         $urlWeb/vivo"
Write-Host "  API (comprobar):                $urlApi/api/salud"
Write-Host "  En este equipo también:         http://localhost:3000"
Write-Host "  Cuentas: docente@demo.com / estudiante@demo.com / coordinador@demo.com  (clave Demo12345)"
Write-Host "===================================================" -ForegroundColor Green
Write-Host "Si otro dispositivo no carga la página, abre el firewall (ver comentario al inicio de este script)."
Write-Host "Pulsa Ctrl+C o Enter para DETENER ambos servidores."
[void](Read-Host)

foreach ($p in $backend, $frontend) {
    if ($p -and -not $p.HasExited) { & taskkill /PID $p.Id /T /F | Out-Null }
}
Write-Host "Servidores detenidos."
