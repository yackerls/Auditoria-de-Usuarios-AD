# 🛡️ AD Identity Auditor

Este proyecto es una herramienta de auditoría para **Active Directory (AD)** local. Permite visualizar de forma rápida el estado de las cuentas de usuario, enfocándose en la seguridad de las contraseñas y el estado de bloqueo de las cuentas.

La solución utiliza un script de **PowerShell** para la extracción de datos y un dashboard interactivo construido en **Streamlit**.

## 🚀 Características principales
* **Control de Contraseñas:** Identifica usuarios que no han cambiado su clave en más de 90 días (3 meses).
* **Cuentas Bloqueadas:** Listado en tiempo real de usuarios bloqueados en el dominio.
* **Métricas de Seguridad:** Resumen visual del estado general de la infraestructura de identidad.
* **Privacidad:** Los datos se procesan en memoria mediante la carga de un archivo JSON; no se almacenan permanentemente en la nube.

---

## 📂 Estructura del Proyecto
* `app.py`: Aplicación principal de Streamlit.
* `requirements.txt`: Dependencias de Python.
* `scripts/`: Contiene el script de PowerShell para la extracción de datos del AD.
* `data/`: Carpeta para almacenar temporalmente el archivo `ad_audit.json` (opcional).

---

## 🛠️ Guía de Instalación y Uso

### Paso 1: Extracción de datos (En el Servidor AD)
Ejecuta el siguiente script en una consola de PowerShell con privilegios de Administrador para generar el reporte:

```powershell
# Definir ruta de salida
$dirPath = "C:\auditoria_data"
if (!(Test-Path $dirPath)) { New-Item -ItemType Directory -Path $dirPath }
$outputPath = Join-Path $dirPath "ad_audit.json"

# Obtener usuarios y exportar
Get-ADUser -Filter * -Properties PasswordLastSet, LockedOut, EmailAddress, DisplayName | Select-Object `
    DisplayName, 
    EmailAddress, 
    @{Name="DiasDesdeCambioClave"; Expression={if($_.PasswordLastSet){((Get-Date) - $_.PasswordLastSet).Days}else{999}}},
    @{Name="UltimaFechaCambio"; Expression={$_.PasswordLastSet}},
    @{Name="Estado"; Expression={if($_.LockedOut){"Bloqueado"}else{"Activo"}}} | 
ConvertTo-Json | Out-File $outputPath -Encoding utf8