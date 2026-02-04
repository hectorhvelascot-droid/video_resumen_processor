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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
