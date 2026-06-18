# Pokemon GO Box Manager

Organizador automático de la caja de Pokémon GO mediante visión artificial.

## Requisitos

- Python **3.11+**
- Windows (los datos de la app se guardan en `%APPDATA%`)

## Instalación

Desde la raíz del proyecto:

```powershell
cd "D:\Proyectos\pkm manager"
python -m pip install -e .
```

Solo para probar la base actual (sin instalar dependencias pesadas como OCR):

```powershell
cd "D:\Proyectos\pkm manager"
python -m app.main
```

## Cómo arrancar

Siempre ejecuta los comandos desde la **raíz del proyecto**, no desde `D:\Proyectos` ni desde la carpeta `app\`.

### Opción 1: módulo Python (recomendada)

```powershell
cd "D:\Proyectos\pkm manager"
python -m app.main
```

### Opción 2: script directo

```powershell
cd "D:\Proyectos\pkm manager"
python app\main.py
```

### Opción 3: comando instalado (tras `pip install -e .`)

```powershell
pokemon-go-box-manager
```

## Salida esperada

Si todo va bien verás algo como:

```text
INFO | app.main | Starting Pokemon GO Box Manager v0.1.0
INFO | app.main | Launching main window
```

Después se abrirá una ventana con:
- estado de la aplicación
- detección de dispositivos Android por ADB
- **captura de pantalla** del móvil
- **escaneo de prueba** con OCR
- contador de Pokémon en base de datos
- ajustes básicos (ADB, OCR, delay de escaneo)

### Captura y escaneo

1. Conecta el móvil por USB y activa depuración USB
2. Abre Pokémon GO en la **ficha del primer Pokémon** de tu caja
3. En la app pulsa **Buscar dispositivos**
4. Pulsa **Iniciar escaneo automático**

La app capturará cada Pokémon, leerá nombre/CP/IV con OCR, lo guardará en la base de datos y pasará al siguiente con un deslizamiento automático. Se detiene sola al volver al primero o puedes pulsar **Detener escaneo**.

También puedes usar **Capturar pantalla** o **Escaneo de prueba** para probar uno solo.

Las capturas se guardan en `%APPDATA%\PokemonGOBoxManager\screenshots\`.

La primera vez que uses OCR puede tardar porque PaddleOCR descarga modelos.

## Errores habituales

| Comando incorrecto | Problema |
|---|---|
| `python -m app.main` desde `D:\Proyectos` | No encuentra el paquete `app` |
| `python -m app.main` desde `app\` | El path no apunta a la raíz del proyecto |
| `python -m app/main.py` | `python -m` usa nombres de módulo, no rutas con `/` o `.py` |
| `pip install -e .` con Python 3.10 o anterior | El proyecto requiere Python 3.11+ |

**Correcto:** `python -m app.main` o `python app\main.py` desde `D:\Proyectos\pkm manager`

## Datos de la aplicación

En Windows se crean en:

- Config: `%APPDATA%\PokemonGOBoxManager\config.json`
- Logs: `%APPDATA%\PokemonGOBoxManager\logs\`
- Exports: `%APPDATA%\PokemonGOBoxManager\exports\`
