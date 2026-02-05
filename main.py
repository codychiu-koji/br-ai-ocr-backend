from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from paddleocr import PaddleOCR
import hashlib
from supabase import create_client, Client

app = FastAPI(title="BR AI OCR Backend - v2.1 FINAL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://odjihllmfnwushmmqmoc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

ocr_engines = {
    "HK": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
    "CN": PaddleOCR(use_angle_cls=True, lang='ch'),
    "MO": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
}

@app.get("/")
@app.get("/health")
async def health_check():
    db_status = "not_configured"
    if supabase:
        try:
            result = supabase.table("api_keys").select("id").limit(1).execute()
            db_status = "connected"
        except Exception as e:
            db_status = f"error: {str(e)}"
    return {
        "status": "healthy",
        "database": db_status,
        "version": "v2.1-final",
        "deployed_via": "railway_up"
    }

@app.get("/version")
async def version_check():
    return {
        "version": "v2.1-final",
        "timestamp": "2026-02-05-1505",
        "status": "✅ NEW VERSION"
    }

def verify_api_key(api_key: str) -> dict:
    if not supabase:
        return {"id": "test", "account_id": "test"}
    try:
        result = supabase.table("api_keys").select("*").eq("key", api_key).eq("is_active", True).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        result = supabase.table("api_keys").select("*").eq("key_hash", key_hash).eq("is_active", True).execute()
        if result.data and len(result.data) > 0:
            return result.data[0]
        return None
    except Exception as e:
        print(f"API Key error: {e}")
        return None

@app.post("/v1/ocr/scan")
async def ocr_scan(file: UploadFile = File(...), region: str = Form(...), api_key: str = Header(None, alias="X-API-Key")):
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    key_data = verify_api_key(api_key)
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    if region not in ["HK", "CN", "MO"]:
        raise HTTPException(status_code=400, detail="Invalid region")
    
    import tempfile, time, uuid
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        start_time = time.time()
        ocr = ocr_engines[region]
        result = ocr.ocr(tmp_path, cls=True)
        processing_time = int((time.time() - start_time) * 1000)
        
        lines = []
        if result and result[0]:
            for line in result[0]:
                lines.append({
                    "text": line[1][0],
                    "confidence": float(line[1][1]),
                    "box": [point for point in line[0]]
                })
        
        avg_confidence = sum(l["confidence"] for l in lines) / len(lines) if lines else 0
        
        return {
            "status": "success",
            "job_id": str(uuid.uuid4()),
            "region": region,
            "lines": lines,
            "total_lines": len(lines),
            "confidence_avg": avg_confidence,
            "processing_time_ms": processing_time
        }
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
