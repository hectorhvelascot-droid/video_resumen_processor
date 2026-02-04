# Guía de Despliegue - Video Resumen Processor

Esta guía te llevará paso a paso para desplegar el procesador de videos en Render, reemplazando tu workflow de N8N.

---

## 📁 Estructura del Proyecto

```
video-processor/
├── main.py              # API FastAPI con endpoint webhook
├── workflow.py          # Lógica de procesamiento
├── requirements.txt     # Dependencias Python
├── render.yaml         # Configuración de Render
└── README.md           # Esta guía
```

---

## PASO 1: Crear repositorio en GitHub

### 1.1 Instalar Git (si no lo tienes)

1. Ve a https://git-scm.com/download/win
2. Descarga e instala Git

### 1.2 Inicializar repositorio local

Abre CMD o PowerShell y ejecuta:

```bash
cd "a:\DEV\notebook lm\video-processor"
git init
```

### 1.3 Crear cuenta en GitHub (si no tienes)

1. Ve a https://github.com
2. Crea cuenta gratuita

### 1.4 Crear repositorio remoto

1. En GitHub haz clic en **"New"** → **"New repository"**
2. **Nombre:** `video-resumen-processor`
3. **Visibilidad:** Público (o privado si prefieres)
4. **NO marques** "Add a README"
5. Clic en **"Create repository"**

### 1.5 Subir código

En la terminal, ejecuta estos comandos en orden:

```bash
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/video-resumen-processor.git
git push -u origin main
```

**Nota:** Reemplaza `TU_USUARIO` con tu nombre de usuario de GitHub.

---

## PASO 2: Crear cuenta en Render

1. Ve a https://render.com
2. Haz clic en **"Get Started for Free"**
3. Elige **"Continue with GitHub"**
4. Autoriza a Render para acceder a tus repositorios

---

## PASO 3: Crear Web Service en Render

1. En el Dashboard de Render, haz clic en **"New +"**
2. Selecciona **"Web Service"**
3. Busca y selecciona tu repositorio `video-resumen-processor`
4. Configura con estos valores:

### Configuración Básica

| Campo | Valor |
|-------|-------|
| **Name** | video-resumen-processor |
| **Region** | Oregon (US West) |
| **Branch** | main |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Plan** | Free |

### Variables de Entorno (IMPORTANTE)

Haz clic en **"Advanced"** para expandir, luego en **"Add Environment Variable"** y añade cada una:

#### Requeridas:

```
YT_API_KEY = tu_api_key_de_youtube
APIFY_TOKEN = tu_apify_token_aqui
GEMINI_KEY = tu_api_key_de_gemini
READWISE_TOKEN = tu_readwise_token_aqui
```

#### Opcionales (para notificaciones):

```
PUSHOVER_TOKEN = tu_token_de_pushover
PUSHOVER_USER = tu_user_key_de_pushover
```

5. Finalmente, clic en **"Create Web Service"**

---

## PASO 4: Esperar el Despliegue

1. Render empezará a construir automáticamente
2. Verás logs en tiempo real en el dashboard
3. Espera a que el estado cambie a **"Live"** en verde
4. Esto toma 2-3 minutos la primera vez
5. Tu URL será algo como: `https://video-resumen-processor.onrender.com`

---

## PASO 5: Verificar que Funciona

### Prueba 1: Health Check

Abre tu navegador y ve a:
```
https://video-resumen-processor.onrender.com/health
```

Deberías ver esta respuesta:
```json
{"status": "ok", "service": "video-processor"}
```

### Prueba 2: Webhook (con curl o Postman)

```bash
curl -X POST https://video-resumen-processor.onrender.com/webhook
```

Respuesta esperada:
```json
{
  "status": "processing",
  "message": "Workflow iniciado",
  "timestamp": "2026-02-04T..."
}
```

---

## PASO 6: Actualizar tu Shortcut de iPhone

1. Abre la app **"Atajos"** en tu iPhone
2. Busca el shortcut que usas actualmente para N8N
3. Encuentra la acción que hace la petición HTTP/webhook
4. Cambia la URL:
   - **Antes:** `https://tu-n8n.render.com/webhook/036ac1ef-...`
   - **Después:** `https://video-resumen-processor.onrender.com/webhook`
5. Guarda el shortcut

---

## PASO 7: Prueba Final desde el iPhone

1. Ejecuta el shortcut desde tu iPhone
2. En 1-2 segundos recibirás respuesta: "Workflow iniciado"
3. El proceso corre en background y puede tardar 2-5 minutos dependiendo de la cantidad de videos
4. Verifica en Readwise que se guardó el nuevo documento

---

## ⚠️ IMPORTANTE: Limitaciones del Plan Gratuito

El plan gratuito de Render tiene una característica importante:

### La App se "Duerme"

- Después de **15 minutos de inactividad**, la app se suspende
- La primera solicitud después de eso tardará **~30-40 segundos** en responder (está "despertando")
- Después de despertar, responde inmediatamente durante 15 minutos

### Soluciones:

**Opción A: Upgrade a $7/mes (Plan Starter)**
- La app nunca duerme
- Responde siempre inmediatamente

**Opción B: UptimeRobot (Gratuito)**
1. Crea cuenta en https://uptimerobot.com
2. Añade un nuevo monitor
3. Tipo: HTTP(s)
4. URL: `https://video-resumen-processor.onrender.com/health`
5. Intervalo de monitoreo: Cada 10 minutos
6. Esto mantiene la app despierta constantemente

---

## 🔧 Troubleshooting

### La app no inicia

**Síntoma:** El deploy falla o el estado no cambia a "Live"

**Solución:**
1. Ve al Dashboard de Render
2. Clic en tu servicio
3. Ve a la pestaña "Logs"
4. Busca errores en rojo
5. Verifica que todas las variables de entorno estén correctas

### El webhook devuelve error 404 o 500

**Solución:**
1. Prueba primero con `/health` para verificar que la app está viva
2. Asegúrate de usar método POST (no GET)
3. Verifica la URL completa esté correcta

### No llegan notificaciones al teléfono

**Para usar Pushover:**
1. Descarga la app "Pushover" en tu iPhone/Android
2. Crea cuenta gratuita en https://pushover.net
3. Obtén tu **User Key** (aparece en la página principal)
4. Crea una nueva aplicación para obtener el **API Token**
5. Agrega ambos como variables de entorno en Render

### El proceso tarda mucho o timeout

**Normal:** El procesamiento completo puede tardar 2-5 minutos dependiendo de:
- Cantidad de videos en la playlist
- Duración de los videos
- Velocidad de Apify

El webhook responde inmediatamente, pero el trabajo continúa en background.

---

## 📱 Notificaciones (Opcional)

Para recibir notificaciones cuando termine el proceso:

1. Instala **Pushover** en tu teléfono
2. Configura las variables `PUSHOVER_TOKEN` y `PUSHOVER_USER`
3. Recibirás notificaciones:
   - 🚀 "Iniciando procesamiento de videos..."
   - ✅ "Video Resumen completado y guardado en Readwise!"
   - ❌ "Error: [descripción del error]"

---

## 📝 Resumen de URLs Importantes

| Servicio | URL |
|----------|-----|
| **Render Dashboard** | https://dashboard.render.com |
| **Tu App** | https://video-resumen-processor.onrender.com |
| **Health Check** | https://video-resumen-processor.onrender.com/health |
| **Webhook** | https://video-resumen-processor.onrender.com/webhook |
| **GitHub** | https://github.com/TU_USUARIO/video-resumen-processor |

---

## 🆘 Soporte

Si tienes problemas:

1. Revisa los logs en Render Dashboard
2. Verifica que todas las API keys sean válidas
3. Prueba localmente primero ejecutando: `python workflow.py`
4. Si todo falla, puedes volver a tu workflow de N8N mientras solucionas

---

**Fecha de creación:** 4 de Febrero de 2026
**Autor:** Asistente Claude (Anthropic)
