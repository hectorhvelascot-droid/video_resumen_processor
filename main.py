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
    """Endpoint de diagnóstico para probar APIs de IA desde Render"""
    import requests as req
    import os
    
    results = {
        "gemini_key_configured": bool(os.getenv("GEMINI_KEY")),
        "gemini_key_preview": (os.getenv("GEMINI_KEY", "")[:10] + "...") if os.getenv("GEMINI_KEY") else "NOT SET",
        "openrouter_key_configured": bool(os.getenv("OPENROUTER_KEY")),
        "openrouter_key_preview": (os.getenv("OPENROUTER_KEY", "")[:12] + "...") if os.getenv("OPENROUTER_KEY") else "NOT SET",
        "server_ip": "unknown",
        "tests": {}
    }
    
    # Obtener IP pública del servidor
    try:
        ip_resp = req.get("https://api.ipify.org?format=json", timeout=5)
        results["server_ip"] = ip_resp.json().get("ip", "unknown")
    except:
        results["server_ip"] = "could not determine"
    
    # Test 1: OpenRouter (proveedor principal)
    openrouter_key = os.getenv("OPENROUTER_KEY", "")
    if openrouter_key:
        try:
            r = req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {openrouter_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "google/gemini-2.0-flash-001",
                    "messages": [{"role": "user", "content": "Responde solo: OK funciono"}],
                    "max_tokens": 50
                },
                timeout=30
            )
            if r.status_code == 200 and 'choices' in r.json():
                text = r.json()['choices'][0]['message']['content']
                results["tests"]["openrouter_gemini"] = {"status": "OK", "response": text[:100]}
            else:
                results["tests"]["openrouter_gemini"] = {"status": "ERROR", "http_code": r.status_code, "response": r.json()}
        except Exception as e:
            results["tests"]["openrouter_gemini"] = {"status": "ERROR", "exception": str(e)}
    else:
        results["tests"]["openrouter_gemini"] = {"status": "SKIP", "reason": "OPENROUTER_KEY not set"}
    
    # Test 2: Gemini directo (fallback)
    api_key = os.getenv("GEMINI_KEY", "")
    if api_key:
        try:
            r = req.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}",
                json={"contents": [{"parts": [{"text": "Responde solo: OK"}]}]},
                timeout=30
            )
            if r.status_code == 200 and 'candidates' in r.json():
                text = r.json()['candidates'][0]['content']['parts'][0]['text']
                results["tests"]["gemini_direct"] = {"status": "OK", "response": text[:100]}
            else:
                results["tests"]["gemini_direct"] = {"status": "ERROR", "http_code": r.status_code, "response": r.json()}
        except Exception as e:
            results["tests"]["gemini_direct"] = {"status": "ERROR", "exception": str(e)}
    else:
        results["tests"]["gemini_direct"] = {"status": "SKIP", "reason": "GEMINI_KEY not set"}
    
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
