import requests
import json
import os
from datetime import datetime

# Obtener credenciales de variables de entorno
YT_API_KEY = os.getenv("YT_API_KEY")
APIFY_TOKEN = os.getenv("APIFY_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_KEY")
READWISE_TOKEN = os.getenv("READWISE_TOKEN")
PUSHOVER_TOKEN = os.getenv("PUSHOVER_TOKEN")
PUSHOVER_USER = os.getenv("PUSHOVER_USER")

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
    for item in data.get('items', []):
        video_id = item['contentDetails']['videoId']
        video_urls.append(f"https://www.youtube.com/watch?v={video_id}")
        titles.append(item['snippet']['title'])
    
    return video_urls, titles

def get_transcripts(video_urls):
    """Obtiene transcripciones con Apify"""
    url = f"https://api.apify.com/v2/acts/karamelo~youtube-transcripts/run-sync-get-dataset-items?token={APIFY_TOKEN}"
    payload = {
        "urls": video_urls,
        "outputFormat": "captions",
        "proxyOptions": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"],
            "apifyProxyCountry": "MX"
        },
        "maxRetries": 8,
        "channelHandleBoolean": True,
        "channelNameBoolean": True,
        "datePublishedBoolean": True,
        "relativeDateTextBoolean": True
    }
    response = requests.post(url, json=payload, timeout=300)
    return response.json()

def summarize_with_gemini(text):
    """Resume texto con Google Gemini"""
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={GEMINI_KEY}"
    
    prompt = f"""Hazme un resumen en español muy completo y que incluya toda la información relevante del siguiente transcript sin hacerme comentarios adicionales porque se va a publicar directo.

IMPORTANTE: Usa formato HTML (no markdown) con etiquetas como <h2>, <h3>, <p>, <b>, <ul>, <li>. No uses ## ni ** ni otros marcadores de markdown.

{text}

Después dame un segundo resumen mucho más detallado que permita ver datos y capaz de información más específicas y de interés particular. Sin hacerme comentarios adicionales porque se va a publicar directo."""
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    
    response = requests.post(url, json=payload)
    data = response.json()
    
    print(f"Respuesta Gemini: {data}")
    
    if 'candidates' in data:
        return data['candidates'][0]['content']['parts'][0]['text']
    elif 'error' in data:
        print(f"Error Gemini: {data['error']}")
        return f"Error al generar resumen: {data['error'].get('message', 'Error desconocido')}"
    return "Error al generar resumen: No se recibieron candidates"

def format_as_html(summary, transcripts, titles):
    """Formatea el contenido como HTML"""
    html = f"""
    <h1>Resumen de Videos</h1>
    <h2>Resumen General</h2>
    <div>{summary}</div>
    <hr>
    <h2>Transcripciones Completas</h2>
    """
    
    for i, (transcript, title) in enumerate(zip(transcripts, titles)):
        html += f"""
        <h3>Video {i+1}: {title}</h3>
        <div>{transcript}</div>
        <hr>
        """
    
    return html

def save_to_readwise(html_content, title):
    """Guarda en Readwise"""
    url = "https://readwise.io/api/v3/save/"
    headers = {"Authorization": f"Token {READWISE_TOKEN}"}
    payload = {
        "url": "https://drive.google.com/drive/folders/1fiXci1ERcnRSN_SfwpJCZA-3z0W63xvC",
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
        video_urls, titles = get_playlist_videos(playlist_id)
        print(f"✅ Encontrados {len(video_urls)} videos")
        
        # Paso 2: Obtener transcripciones
        print("📝 Obteniendo transcripciones...")
        transcripts_data = get_transcripts(video_urls)
        print("✅ Transcripciones obtenidas")
        
        # Extraer captions
        captions = []
        for item in transcripts_data:
            if 'captions' in item and item['captions']:
                # Unir todos los textos de los captions en un solo string
                caption_texts = [caption['text'] if isinstance(caption, dict) and 'text' in caption else str(caption) for caption in item['captions']]
                full_transcript = " ".join(caption_texts)
                captions.append(full_transcript)
        
        all_text = " ".join(captions)
        
        # Paso 3: Resumir
        print("🤖 Generando resumen con Gemini...")
        summary = summarize_with_gemini(all_text)
        print("✅ Resumen generado")
        
        # Paso 4: Formatear HTML
        print("🎨 Formateando HTML...")
        html_content = format_as_html(summary, captions, titles)
        
        # Paso 5: Guardar en Readwise
        print("💾 Guardando en Readwise...")
        result = save_to_readwise(html_content, f"Video Resumen - {datetime.now().strftime('%Y-%m-%d')}")
        print(f"✅ Guardado en Readwise: {result}")
        
        send_notification("✅ Video Resumen completado y guardado en Readwise!")
        print(f"[{datetime.now()}] ✅ Proceso completado exitosamente")
        
    except Exception as e:
        error_msg = f"❌ Error en workflow: {str(e)}"
        print(f"[{datetime.now()}] {error_msg}")
        send_notification(error_msg)
        raise

if __name__ == "__main__":
    process_playlist()
