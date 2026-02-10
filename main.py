from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import workflow
import asyncio
from datetime import datetime

app = FastAPI(title="Video Resumen Processor")

@app.post("/webhook")
async def trigger_processing():
    """
    Endpoint que reemplaza tu webhook de N8N.
    Lo llamas desde el shortcut de tu teléfono.
    Procesa una playlist completa.
    """
    try:
        # Ejecutar el workflow en background para no timeout
        asyncio.create_task(run_workflow_async())
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "processing",
                "message": "Workflow iniciado",
                "timestamp": datetime.now().isoformat()
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/telegram")
async def telegram_webhook(request: Request):
    """
    Endpoint para recibir webhooks de Telegram.
    Procesa un video individual enviado por Telegram.
    """
    try:
        data = await request.json()
        
        # Extraer datos del mensaje de Telegram
        if "message" in data and "text" in data["message"]:
            video_url = data["message"]["text"]
            chat_id = data["message"]["chat"]["id"]
            
            # Verificar que sea una URL de YouTube
            if "youtube.com" in video_url or "youtu.be" in video_url:
                # Ejecutar procesamiento en background
                asyncio.create_task(run_telegram_workflow_async(video_url, chat_id))
                
                return JSONResponse(
                    status_code=200,
                    content={"status": "processing", "message": "Video recibido"}
                )
            else:
                # Enviar mensaje de error por Telegram
                asyncio.create_task(
                    asyncio.to_thread(workflow.send_telegram_message, chat_id, "Por favor envía una URL válida de YouTube.")
                )
                return JSONResponse(
                    status_code=400,
                    content={"status": "error", "message": "URL inválida"}
                )
        
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Formato inválido"}
        )
        
    except Exception as e:
        print(f"[{datetime.now()}] Error en webhook Telegram: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def run_workflow_async():
    """Ejecuta el workflow de playlist sin bloquear la respuesta HTTP"""
    try:
        await asyncio.to_thread(workflow.process_playlist)
        print(f"[{datetime.now()}] Workflow de playlist completado exitosamente")
    except Exception as e:
        print(f"[{datetime.now()}] Error en workflow de playlist: {e}")

async def run_telegram_workflow_async(video_url: str, chat_id: int):
    """Ejecuta el workflow de Telegram sin bloquear la respuesta HTTP"""
    try:
        await asyncio.to_thread(workflow.process_video_from_telegram, video_url, chat_id)
        print(f"[{datetime.now()}] Workflow de Telegram completado exitosamente")
    except Exception as e:
        print(f"[{datetime.now()}] Error en workflow de Telegram: {e}")
        # Notificar error por Telegram
        await asyncio.to_thread(workflow.send_telegram_message, chat_id, f"❌ Error al procesar el video: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "video-processor"}

@app.get("/test-gemini")
async def test_gemini():
    """Endpoint de diagnóstico para probar la API key de Gemini desde Render"""
    import requests as req
    import os
    
    results = {
        "gemini_key_configured": bool(os.getenv("GEMINI_KEY")),
        "gemini_key_preview": (os.getenv("GEMINI_KEY", "")[:10] + "...") if os.getenv("GEMINI_KEY") else "NOT SET",
        "gemini_key_length": len(os.getenv("GEMINI_KEY", "")),
        "server_ip": "unknown",
        "tests": {}
    }
    
    # Obtener IP pública del servidor
    try:
        ip_resp = req.get("https://api.ipify.org?format=json", timeout=5)
        results["server_ip"] = ip_resp.json().get("ip", "unknown")
    except:
        results["server_ip"] = "could not determine"
    
    api_key = os.getenv("GEMINI_KEY", "")
    if not api_key:
        results["error"] = "GEMINI_KEY environment variable is not set"
        return results
    
    # Test 1: Listar modelos
    try:
        r = req.get(f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}", timeout=15)
        if r.status_code == 200:
            models = [m['name'] for m in r.json().get('models', []) if 'gemini' in m['name'].lower()]
            results["tests"]["list_models"] = {"status": "OK", "models_count": len(models)}
        else:
            results["tests"]["list_models"] = {"status": "ERROR", "http_code": r.status_code, "response": r.json()}
    except Exception as e:
        results["tests"]["list_models"] = {"status": "ERROR", "exception": str(e)}
    
    # Test 2: Generar contenido v1beta
    try:
        r = req.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": "Responde solo: OK"}]}]},
            timeout=30
        )
        if r.status_code == 200 and 'candidates' in r.json():
            text = r.json()['candidates'][0]['content']['parts'][0]['text']
            results["tests"]["v1beta_generate"] = {"status": "OK", "response": text[:100]}
        else:
            results["tests"]["v1beta_generate"] = {"status": "ERROR", "http_code": r.status_code, "response": r.json()}
    except Exception as e:
        results["tests"]["v1beta_generate"] = {"status": "ERROR", "exception": str(e)}
    
    # Test 3: v1 endpoint
    try:
        r = req.post(
            f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": "Responde solo: OK"}]}]},
            timeout=30
        )
        if r.status_code == 200 and 'candidates' in r.json():
            text = r.json()['candidates'][0]['content']['parts'][0]['text']
            results["tests"]["v1_generate"] = {"status": "OK", "response": text[:100]}
        else:
            results["tests"]["v1_generate"] = {"status": "ERROR", "http_code": r.status_code, "response": r.json()}
    except Exception as e:
        results["tests"]["v1_generate"] = {"status": "ERROR", "exception": str(e)}
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
