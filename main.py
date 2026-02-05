from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from paddleocr import PaddleOCR
import hashlib
from supabase import create_client, Client

app = FastAPI(title="BR AI OCR Backend v2.1")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://odjihllmfnwushmmqmoc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

ocr_engines = {
    "HK": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
    "CN": PaddleOCR(use_angle_cls=True, lang='ch'),
    "MO": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
}

@app.get("/")
def root():
    return {"message": "BR AI OCR Backend v2.1", "status": "online"}

@app.get("/health")
def health():
    db = "not_configured"
    if supabase:
        try:
            supabase.table("api_keys").select("id").limit(1).execute()
            db = "connected"
        except:
            db = "error"
    return {"status": "healthy", "database": db, "version": "v2.1"}

@app.get("/version")
def version():
    return {"version": "v2.1", "timestamp": "2026-02-05-1519", "status": "NEW"}

def verify_api_key(key: str):
    if not supabase:
        return {"id": "test"}
    try:
        r = supabase.table("api_keys").select("*").eq("key", key).eq("is_active", True).execute()
        if r.data:
            return r.data[0]
        h = hashlib.sha256(key.encode()).hexdigest()
        r = supabase.table("api_keys").select("*").eq("key_hash", h).eq("is_active", True).execute()
        return r.data[0] if r.data else None
    except:
        return None

@app.post("/v1/ocr/scan")
async def scan(file: UploadFile = File(...), region: str = Form(...), api_key: str = Header(None, alias="X-API-Key")):
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(403, "Invalid API Key")
    if region not in ["HK", "CN", "MO"]:
        raise HTTPException(400, "Invalid region")
    
    import tempfile, time, uuid
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    try:
        start = time.time()
        result = ocr_engines[region].ocr(tmp_path, cls=True)
        ms = int((time.time() - start) * 1000)
        
        lines = []
        if result and result[0]:
            for line in result[0]:
                lines.append({"text": line[1][0], "confidence": float(line[1][1]), "box": [p for p in line[0]]})
        
        avg = sum(l["confidence"] for l in lines) / len(lines) if lines else 0
        return {"status": "success", "job_id": str(uuid.uuid4()), "region": region, "lines": lines, "total_lines": len(lines), "confidence_avg": avg, "processing_time_ms": ms}
    finally:
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
