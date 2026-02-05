from fastapi import FastAPI, File, UploadFile, Form, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from paddleocr import PaddleOCR
import hashlib
from supabase import create_client, Client

app = FastAPI(title="BR AI OCR Backend")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://br-ai-ocr-frontend.vercel.app",
        "*"  # 暫時允許所有 origins（測試用）
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://odjihllmfnwushmmqmoc.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "your-service-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# PaddleOCR
ocr_engines = {
    "HK": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
    "CN": PaddleOCR(use_angle_cls=True, lang='ch'),
    "MO": PaddleOCR(use_angle_cls=True, lang='chinese_cht'),
}

@app.get("/health")
async def health_check():
    try:
        # 測試 Supabase 連接
        result = supabase.table("api_keys").select("id").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "healthy", "database": f"error: {str(e)}"}

def verify_api_key(api_key: str) -> dict:
    """驗證 API Key（支援明文 key 欄位）"""
    try:
        # 方法 1: 直接比對明文 key（如果 schema 有 key 欄位）
        result = supabase.table("api_keys")\
            .select("*")\
            .eq("key", api_key)\
            .eq("is_active", True)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        # 方法 2: 用 SHA256 hash 比對
        key_hash = hashlib.sha256(api_key.encode()).hexdigest()
        result = supabase.table("api_keys")\
            .select("*")\
            .eq("key_hash", key_hash)\
            .eq("is_active", True)\
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return None
    except Exception as e:
        print(f"API Key verification error: {e}")
        return None

@app.post("/v1/ocr/scan")
async def ocr_scan(
    file: UploadFile = File(...),
    region: str = Form(...),
    api_key: str = Header(None, alias="X-API-Key")
):
    # 驗證 API Key
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API Key")
    
    key_data = verify_api_key(api_key)
    if not key_data:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    
    # 檢查 region
    if region not in ["HK", "CN", "MO"]:
        raise HTTPException(status_code=400, detail="Invalid region")
    
    # 讀取圖片
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # OCR 辨識
        import time
        start_time = time.time()
        
        ocr = ocr_engines[region]
        result = ocr.ocr(tmp_path, cls=True)
        
        processing_time = int((time.time() - start_time) * 1000)
        
        # 解析結果
        lines = []
        if result and result[0]:
            for line in result[0]:
                text = line[1][0]
                confidence = float(line[1][1])
                box = [point for point in line[0]]
                lines.append({
                    "text": text,
                    "confidence": confidence,
                    "box": box
                })
        
        # 計算平均準確度
        avg_confidence = sum(l["confidence"] for l in lines) / len(lines) if lines else 0
        
        # 儲存到資料庫（可選）
        import uuid
        job_id = str(uuid.uuid4())
        
        return {
            "status": "success",
            "job_id": job_id,
            "region": region,
            "lines": lines,
            "total_lines": len(lines),
            "confidence_avg": avg_confidence,
            "processing_time_ms": processing_time
        }
        
    finally:
        # 清理臨時檔案
        import os
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
