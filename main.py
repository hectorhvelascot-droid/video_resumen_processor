from fastapi import FastAPI, HTTPException
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

async def run_workflow_async():
    """Ejecuta el workflow sin bloquear la respuesta HTTP"""
    try:
        await asyncio.to_thread(workflow.process_playlist)
        print(f"[{datetime.now()}] Workflow completado exitosamente")
    except Exception as e:
        print(f"[{datetime.now()}] Error en workflow: {e}")

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "video-processor"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
