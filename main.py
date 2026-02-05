from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os, hashlib, tempfile, time, uuid
from supabase import create_client

app = FastAPI(title="BR AI OCR v2.2 - Lazy Loading")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://odjihllmfnwushmmqmoc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None

# 🔧 改用 Lazy Loading - 不在啟動時初始化
ocr_engines = {}

def get_ocr_engine(region: str):
    """延遲初始化 OCR engine（只在需要時才初始化）"""
    if region not in ocr_engines:
        from paddleocr import PaddleOCR
        print(f"🔧 初始化 OCR engine: {region}")
        lang_map = {"HK": "chinese_cht", "CN": "ch", "MO": "chinese_cht"}
        # 禁用 CPU 優化，避免 SIGILL 錯誤
        ocr_engines[region] = PaddleOCR(
            use_angle_cls=True,
            lang=lang_map[region],
            enable_mkldnn=False,  # 禁用 MKL-DNN
            ir_optim=False,       # 禁用 IR 優化
            use_gpu=False,
            show_log=False
        )
    return ocr_engines[region]

@app.get("/")
@app.get("/health")
def health():
    db = "ok"
    if supabase:
        try:
            supabase.table("api_keys").select("id").limit(1).execute()
        except:
            db = "error"
    return {
        "status": "healthy",
        "database": db,
        "version": "v2.2-lazy-loading",
        "message": "OCR engines will be initialized on first request"
    }

@app.get("/version")
def version():
    return {"version": "v2.2-lazy-loading", "time": "2026-02-05-1600"}

def verify_key(k):
    if not supabase: return {"id": "test"}
    try:
        r = supabase.table("api_keys").select("*").eq("key", k).eq("is_active", True).execute()
        if r.data: return r.data[0]
        h = hashlib.sha256(k.encode()).hexdigest()
        r = supabase.table("api_keys").select("*").eq("key_hash", h).eq("is_active", True).execute()
        return r.data[0] if r.data else None
    except:
        return None

@app.post("/v1/ocr/scan")
async def scan(file: UploadFile = File(...), region: str = Form(...), api_key: str = Header(None, alias="X-API-Key")):
    if not api_key or not verify_key(api_key):
        raise HTTPException(403, "Invalid API Key")
    if region not in ["HK", "CN", "MO"]:
        raise HTTPException(400, "Invalid region")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name
    
    try:
        start = time.time()
        # 🔧 Lazy loading: 只在需要時才初始化 OCR engine
        ocr = get_ocr_engine(region)
        result = ocr.ocr(tmp_path, cls=True)
        ms = int((time.time() - start) * 1000)
        
        lines = []
        if result and result[0]:
            for line in result[0]:
                lines.append({"text": line[1][0], "confidence": float(line[1][1])})
        
        avg = sum(l["confidence"] for l in lines) / len(lines) if lines else 0
        print(f"✅ OCR completed: {len(lines)} lines in {ms}ms")
        
        return {
            "status": "success",
            "job_id": str(uuid.uuid4()),
            "region": region,
            "lines": lines,
            "total_lines": len(lines),
            "confidence_avg": avg,
            "processing_time_ms": ms
        }
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
