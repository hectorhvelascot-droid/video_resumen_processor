import requests
import json
import os
import time
from datetime import datetime

# Obtener credenciales de variables de entorno
YT_API_KEY = os.getenv("YT_API_KEY")
YT_CLIENT_ID = os.getenv("YT_CLIENT_ID")
YT_CLIENT_SECRET = os.getenv("YT_CLIENT_SECRET")
YT_REFRESH_TOKEN = os.getenv("YT_REFRESH_TOKEN")

APIFY_TOKEN = os.getenv("APIFY_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def send_notification(message):
    """Envía notificación a tu teléfono"""
    if PUSHOVER_TOKEN and PUSHOVER_USER:
        try:
            requests.post("https://api.pushover.net/1/messages.json", json={
                "token": PUSHOVER_TOKEN,
                "user": PUSHOVER_USER,
                "message": message
            })
        except:
            pass

def send_telegram_message(chat_id, message):
    """Envía mensaje a Telegram"""
    if TELEGRAM_BOT_TOKEN:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
            requests.post(url, json={
                "chat_id": chat_id,
                "text": message,
                "parse_mode": "HTML"
            })
        except Exception as e:
            print(f"Error enviando mensaje a Telegram: {e}")

def get_video_info(video_url):
    """Obtiene información de un video de YouTube individual"""
    # Extraer video ID de la URL
    if "v=" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[1].split("?")[0]
    else:
        raise ValueError("URL de YouTube no válida")
    
    # Obtener información del video
    url = "https://www.googleapis.com/youtube/v3/videos"
    params = {
        "part": "snippet",
        "id": video_id,
        "key": YT_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get('items'):
        return {
            'video_id': video_id,
            'title': data['items'][0]['snippet']['title'],
            'channel': data['items'][0]['snippet']['channelTitle']
        }
    else:
        raise ValueError("No se pudo obtener información del video")

def process_video_from_telegram(video_url, chat_id):
    """Procesa un video individual enviado desde Telegram"""
    try:
        print(f"[{datetime.now()}] 🚀 Iniciando procesamiento desde Telegram...")
        send_telegram_message(chat_id, "🚀 <b>Procesando video...</b>\nExtrayendo información y transcripción")
        
        # Obtener información del video
        video_info = get_video_info(video_url)
        print(f"📹 Video: {video_info['title']}")
        
        # Obtener transcripción
        print("📝 Obteniendo transcripción...")
        transcripts_data = get_transcripts([video_url])
        print(f"Respuesta Apify: {json.dumps(transcripts_data)[:500]}...")  # Log de debug
        
        # Extraer transcripciones
        captions = []
        
        # Manejar diferentes formatos de respuesta
        if isinstance(transcripts_data, list):
            for item in transcripts_data:
                print(f"Procesando item tipo: {type(item)}")
                
                if isinstance(item, dict):
                    # Formato con campo 'text' (nuevo formato simplificado)
                    if 'text' in item and item['text']:
                        transcript_text = item['text']
                        print(f"Transcript encontrado (formato text): {len(transcript_text)} caracteres")
                        captions.append(transcript_text)
                    # Formato antiguo con 'captions'
                    elif 'captions' in item and item['captions']:
                        caption_list = item['captions']
                        print(f"Captions encontrados: {len(caption_list)} items")
                        
                        caption_texts = []
                        for caption in caption_list:
                            if isinstance(caption, dict) and 'text' in caption:
                                caption_texts.append(caption['text'])
                            elif isinstance(caption, str):
                                caption_texts.append(caption)
                            else:
                                caption_texts.append(str(caption))
                        
                        full_transcript = " ".join(caption_texts)
                        print(f"Transcript extraído: {len(full_transcript)} caracteres")
                        captions.append(full_transcript)
                    else:
                        print(f"Keys disponibles: {item.keys()}")
                elif isinstance(item, str):
                    # Si el item es directamente un string
                    print(f"Transcript como string: {len(item)} caracteres")
                    captions.append(item)
        elif isinstance(transcripts_data, dict):
            print(f"Respuesta es dict con keys: {transcripts_data.keys()}")
            if 'text' in transcripts_data:
                captions.append(transcripts_data['text'])
        
        if not captions:
            print(f"Respuesta completa de Apify: {json.dumps(transcripts_data)[:1000]}")
            raise ValueError("No se pudo obtener la transcripción del video")
        
        all_text = " ".join(captions)
        print(f"Texto total para resumen: {len(all_text)} caracteres")
        print(f"Texto total para resumen: {len(all_text)} caracteres")
        
        # Generar resumen
        print("🤖 Generando resumen con Gemini...")
        send_telegram_message(chat_id, "🤖 <b>Generando resumen con IA...</b>")
        summary = summarize_with_gemini(all_text)
        print("✅ Resumen generado")
        
        # Formatear HTML
        print("🎨 Formateando HTML...")
        html_content = format_as_html(summary, captions, [video_info['title']], video_url)
        
        # Guardar en Readwise
        print("💾 Guardando en Readwise...")
        send_telegram_message(chat_id, "💾 <b>Guardando en Readwise...</b>")
        result = save_to_readwise(html_content, f"Video - {video_info['title']}", video_url)
        print(f"✅ Guardado en Readwise: {result}")
        
        # Notificar éxito
        send_telegram_message(chat_id, f"✅ <b>¡Listo!</b>\n\n📹 <b>{video_info['title']}</b>\n👤 {video_info['channel']}\n\nEl resumen ha sido guardado en Readwise.")
        print(f"[{datetime.now()}] ✅ Proceso completado exitosamente")
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"[{datetime.now()}] {error_msg}")
        send_telegram_message(chat_id, error_msg)
        raise

def get_playlist_videos(playlist_id):
    """Obtiene videos de playlist de YouTube"""
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "contentDetails,snippet",
        "playlistId": playlist_id,
        "maxResults": 50,
        "key": YT_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    video_urls = []
    titles = []
    video_ids = []
    playlist_item_ids = [] # Necesario para borrarlos después
    
    for item in data.get('items', []):
        video_id = item['contentDetails']['videoId']
        item_id = item['id'] # El ID único de este elemento en esta playlist
        
        video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
        titles.append(item['snippet']['title'])
        video_ids.append(video_id)
        playlist_item_ids.append(item_id)
    
    return video_urls, titles, video_ids, playlist_item_ids
    
def _get_youtube_access_token():
    """Obtiene un token de acceso fresco usando OAuth 2.0 y el Refresh Token"""
    if not all([YT_CLIENT_ID, YT_CLIENT_SECRET, YT_REFRESH_TOKEN]):
        raise ValueError("Faltan credenciales de OAuth para YouTube (Client ID, Client Secret o Refresh Token).")
        
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": YT_CLIENT_ID,
        "client_secret": YT_CLIENT_SECRET,
        "refresh_token": YT_REFRESH_TOKEN,
        "grant_type": "refresh_token"
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    tokens = response.json()
    return tokens.get("access_token")

def clear_playlist_items(playlist_item_ids):
    """Elimina los videos de la playlist de YouTube"""
    if not playlist_item_ids:
        print("No hay items para borrar de la playlist.")
        return
        
    try:
        access_token = _get_youtube_access_token()
    except Exception as e:
        print(f"❌ Error obteniendo token de acceso para YouTube: {e}")
        return
        
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    
    deleted_count = 0
    for item_id in playlist_item_ids:
        try:
            response = requests.delete(f"{url}?id={item_id}", headers=headers)
            if response.status_code == 204:
                deleted_count += 1
                print(f"🗑️ Eliminado item {item_id} de la playlist")
            else:
                print(f"⚠️ Error eliminando {item_id}: {response.status_code} - {response.text}")
        except Exception as e:
            print(f"❌ Excepción al eliminar {item_id}: {e}")
            
    print(f"🧹 Se eliminaron {deleted_count} de {len(playlist_item_ids)} videos de la playlist.")

def get_transcripts(video_urls):
    """Obtiene transcripciones con Apify"""
    url = f"https://api.apify.com/v2/acts/karamelo~youtube-transcripts/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    
    # Payload completo sin especificar país (para evitar error de proxy)
    payload = {
        "urls": video_urls,
        "outputFormat": "captions",
        "proxyOptions": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
            # NOTA: No especificamos país para evitar errores de disponibilidad
        },
        "maxRetries": 3,
        "channelHandleBoolean": True,
        "channelNameBoolean": True,
        "datePublishedBoolean": True,
        "relativeDateTextBoolean": True
    }
    
    print(f"Enviando petición a Apify con URLs: {video_urls}")
    response = requests.post(url, json=payload, timeout=300)
    
    # Verificar si la respuesta es exitosa (200 o 201 son OK)
    if response.status_code not in [200, 201]:
        print(f"Error HTTP {response.status_code}: {response.text}")
        raise ValueError(f"Apify returned HTTP {response.status_code}")
    
    result = response.json()
    
    # Verificar si hay error en la respuesta
    if isinstance(result, dict) and 'error' in result:
        print(f"Error de Apify: {result['error']}")
        raise ValueError(f"Apify error: {result['error']}")
    
    return result

def _build_summary_prompt(text, video_title):
    """Construye el prompt para generar el resumen"""
    return f"""Analiza el siguiente transcript del video "{video_title}" y genera DOS NIVELES DE ANÁLISIS en formato HTML puro (no markdown):

NIVEL 1 - RESUMEN EJECUTIVO (Muy Consolidado):
- Máximo 3-5 puntos clave
- Lo esencial, sin detalles
- Ideal para leer en 30 segundos
- Usa <h3> para el título y <ul><li> para los puntos

NIVEL 2 - ANÁLISIS DETALLADO (Desarrollado):
- Todos los temas principales desarrollados
- Datos específicos, cifras, nombres, fechas
- Estructura por secciones con <h3> y <h4>
- Incluye contexto y relación entre ideas
- Usa <p> para párrafos y <b> para énfasis

FORMATO REQUERIDO:
<h2>NIVEL 1: Resumen Ejecutivo - {video_title}</h2>
[contenido]

<h2>NIVEL 2: Análisis Detallado - {video_title}</h2>
[contenido]

IMPORTANTE: 
- Solo HTML válido, NO uses markdown (##, **, etc.)
- No agregues comentarios introductorios ni de cierre
- El contenido debe estar listo para publicar directo

TRANSCRIPT:
{text}"""

def _call_openrouter(prompt):
    """Llama a Gemini a través de OpenRouter (evita bloqueo de IP)"""
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://video-resumen-processor.onrender.com",
        "X-Title": "Video Resumen Processor"
    }
    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 8000
    }
    
    response = requests.post(url, headers=headers, json=payload, timeout=120)
    data = response.json()
    
    if response.status_code != 200:
        error_msg = data.get('error', {}).get('message', f'HTTP {response.status_code}')
        raise ValueError(f"OpenRouter error: {error_msg}")
    
    if 'choices' in data and len(data['choices']) > 0:
        return data['choices'][0]['message']['content']
    else:
        raise ValueError(f"OpenRouter: respuesta inesperada: {json.dumps(data)[:300]}")

def _call_gemini_direct(prompt):
    """Llama directamente a la API de Gemini"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, json=payload, timeout=120)
    data = response.json()
    
    if response.status_code != 200:
        error_msg = data.get('error', {}).get('message', f'HTTP {response.status_code}')
        raise ValueError(f"Gemini API error: {error_msg}")
    
    if 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text']
    elif 'error' in data:
        raise ValueError(f"Gemini error: {data['error'].get('message', 'Error desconocido')}")
    else:
        raise ValueError("Gemini: No se recibieron candidates en la respuesta")

def summarize_with_gemini(text, video_title="Video", max_retries=3):
    """Resume texto usando OpenRouter (primario) o Gemini directo (fallback)"""
    prompt = _build_summary_prompt(text, video_title)
    
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            # Intentar con OpenRouter primero (evita bloqueo de IP de Render)
            if OPENROUTER_KEY:
                print(f"Intento {attempt}/{max_retries} via OpenRouter...")
                result = _call_openrouter(prompt)
                print("✅ Resumen generado via OpenRouter")
                return result
            
            # Fallback: Gemini directo (funciona localmente, puede fallar en Render)
            if GEMINI_KEY:
                print(f"Intento {attempt}/{max_retries} via Gemini directo...")
                result = _call_gemini_direct(prompt)
                print("✅ Resumen generado via Gemini directo")
                return result
            
            raise ValueError("No hay API key configurada. Configura OPENROUTER_KEY o GEMINI_KEY.")
            
        except ValueError as e:
            last_error = str(e)
            print(f"❌ Error (intento {attempt}): {e}")
            
            # Si OpenRouter falló, intentar Gemini directo como fallback
            if OPENROUTER_KEY and GEMINI_KEY and 'OpenRouter' in str(e):
                try:
                    print(f"Intentando fallback con Gemini directo...")
                    result = _call_gemini_direct(prompt)
                    print("✅ Resumen generado via Gemini directo (fallback)")
                    return result
                except ValueError as e2:
                    print(f"❌ Fallback Gemini también falló: {e2}")
                    last_error = f"OpenRouter: {e} | Gemini: {e2}"
            
            if attempt < max_retries:
                wait_time = attempt * 3
                print(f"Esperando {wait_time}s antes de reintentar...")
                time.sleep(wait_time)
            
        except requests.exceptions.RequestException as e:
            last_error = str(e)
            print(f"Error de conexión (intento {attempt}): {e}")
            if attempt < max_retries:
                time.sleep(attempt * 3)
    
    raise ValueError(f"Error al generar resumen después de {max_retries} intentos: {last_error}")

def summarize_multiple_videos(transcripts, titles):
    """Resume múltiples videos y combina los resultados"""
    all_summaries = []
    
    for i, (transcript, title) in enumerate(zip(transcripts, titles)):
        print(f"🤖 Generando resumen para video {i+1}/{len(titles)}: {title}")
        summary = summarize_with_gemini(transcript, title)
        all_summaries.append(summary)
    
    # Combinar todos los resúmenes
    combined_summary = "\n\n".join(all_summaries)
    return combined_summary

def format_as_html(summary, transcripts, titles, video_url=None):
    """Formatea el contenido como HTML con 3 niveles de análisis"""
    html = f"""
    <h1>Análisis de Videos</h1>
    """
    
    if video_url:
        html += f'<p><b>🔗 Ver video:</b> <a href="{video_url}">{video_url}</a></p>'
    
    html += f"""
    {summary}
    
    <hr>
    <h2>NIVEL 3: Transcript Completo (Búsqueda de Detalles)</h2>
    <p><i>Este nivel contiene el transcript íntegro para buscar información muy específica que no esté en los niveles anteriores.</i></p>
    """
    
    for i, (transcript, title) in enumerate(zip(transcripts, titles)):
        html += f"""
        <h3>Video {i+1}: {title}</h3>
        <div style="background-color: #f5f5f5; padding: 10px; border-left: 3px solid #ccc;">
            {transcript}
        </div>
        <hr>
        """
    
    return html

def save_to_readwise(html_content, title, video_url=None):
    """Guarda en Readwise"""
    url = "https://readwise.io/api/v3/save/"
    headers = {"Authorization": f"Token {READWISE_TOKEN}"}
    
    # Usar la URL del video si se proporciona, sino usar la URL por defecto
    article_url = video_url if video_url else "https://drive.google.com/drive/folders/1fiXci1ERcnRSN_SfwpJCZA-3z0W63xvC"
    
    payload = {
        "url": article_url,
        "html": html_content,
        "title": title,
        "author": "Video Resumen",
        "category": "video",
        "location": "new",
        "saved_using": "python-api"
    }
    response = requests.post(url, headers=headers, json=payload)
    return response.json()

def process_playlist():
    """Ejecuta el workflow completo"""
    playlist_id = "PL_0E-MP0df5mxMX0NrZxSCufMcK6e9z3b"
    
    try:
        print(f"[{datetime.now()}] 🚀 Iniciando procesamiento...")
        send_notification("🚀 Iniciando procesamiento de videos...")
        
        # Paso 1: Obtener videos
        print("📹 Obteniendo videos de la playlist...")
        video_urls, titles, video_ids, playlist_item_ids = get_playlist_videos(playlist_id)
        print(f"✅ Encontrados {len(video_urls)} videos")
        print(f"Video IDs: {video_ids}")
        print(f"Títulos: {titles}")
        
        # Paso 2: Obtener transcripciones
        print("📝 Obteniendo transcripciones...")
        transcripts_data = get_transcripts(video_urls)
        print("✅ Transcripciones obtenidas")
        
        # Extraer captions y emparejar con video_ids
        captions = []
        captions_map = {}  # Mapa video_id -> transcript
        
        for item in transcripts_data:
            if isinstance(item, dict):
                # Obtener el video_id de este item
                item_video_id = item.get('videoId') or item.get('id')
                
                if 'captions' in item and item['captions']:
                    # Unir todos los textos de los captions en un solo string
                    caption_texts = [caption['text'] if isinstance(caption, dict) and 'text' in caption else str(caption) for caption in item['captions']]
                    full_transcript = " ".join(caption_texts)
                    
                    if item_video_id:
                        captions_map[item_video_id] = full_transcript
                        print(f"Transcript asignado a video_id: {item_video_id}")
                    else:
                        # Si no hay video_id, agregar a la lista en orden
                        captions.append(full_transcript)
        
        # Reconstruir la lista de captions en el orden correcto de video_ids
        if captions_map:
            captions = []
            for vid_id in video_ids:
                if vid_id in captions_map:
                    captions.append(captions_map[vid_id])
                else:
                    print(f"⚠️ No se encontró transcript para video_id: {vid_id}")
                    captions.append("")
        
        print(f"Total de captions extraídos: {len(captions)}")
        
        # Paso 3: Resumir cada video individualmente
        print("🤖 Generando resúmenes con Gemini...")
        summary = summarize_multiple_videos(captions, titles)
        print("✅ Resúmenes generados")
        
        # Paso 4: Formatear HTML
        print("🎨 Formateando HTML...")
        html_content = format_as_html(summary, captions, titles, None)
        
        # Paso 5: Guardar en Readwise
        print("💾 Guardando en Readwise...")
        result = save_to_readwise(html_content, f"Video Resumen - {datetime.now().strftime('%Y-%m-%d')}", None)
        print(f"✅ Guardado en Readwise: {result}")
        
        # Paso 6: Limpiar la playlist
        print("🧹 Limpiando la playlist en YouTube...")
        clear_playlist_items(playlist_item_ids)
        
        send_notification("✅ Video Resumen completado, guardado en Readwise y playlist limpiada!")
        print(f"[{datetime.now()}] ✅ Proceso completado exitosamente")
        
    except Exception as e:
        error_msg = f"❌ Error en workflow: {str(e)}"
        print(f"[{datetime.now()}] {error_msg}")
        send_notification(error_msg)
        raise

if __name__ == "__main__":
    process_playlist()
