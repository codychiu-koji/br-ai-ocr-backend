from fastapi import FastAPI, File, UploadFile, HTTPException, Header, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from paddleocr import PaddleOCR
from supabase import create_client, Client
import os
import hashlib
import time
import uuid
from datetime import datetime
from pydantic import BaseModel

app = FastAPI(title="BR AI OCR", version="2.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Supabase client
SUPABASE_URL = "https://odjihllmfnwushmmqmoc.supabase.co"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9kamlobGxtZm53dXNobW1xbW9jIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2ODgwODQ5MywiZXhwIjoyMDg0Mzg0NDkzfQ.NfZ3KpbWkxyOJaqPs5ZbhQYUBL2QpiksjzYMa1xlJ_c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

print("=" * 60)
print("🚀 初始化 OCR Engines...")

ocr_engines = {
    "HK": PaddleOCR(lang='chinese_cht'),
    "CN": PaddleOCR(lang='ch'),
    "MO": PaddleOCR(lang='chinese_cht')
}

print("✅ OCR 已就緒")
print("=" * 60)

# ==================== 認證中間件 ====================
async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """驗證 API Key"""
    try:
        print(f"🔍 驗證 API Key: {x_api_key[:10]}...")
        
        key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        result = supabase.table("api_keys").select("*").eq("key_hash", key_hash).eq("is_active", True).execute()
        
        if not result.data:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        api_key = result.data[0]
        print(f"✅ API Key 驗證成功: {api_key['id']}")
        
        supabase.table("api_keys").update({
            "last_used_at": datetime.now().isoformat()
        }).eq("id", api_key["id"]).execute()
        
        return api_key
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 認證錯誤: {e}")
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

# ==================== API Endpoints ====================

@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head><title>BR AI OCR API v2.0</title></head>
        <body>
            <h1>🚀 BR AI OCR API v2.0</h1>
            <p>✅ Status: Running</p>
            <p>📚 Docs: <a href="/docs">/docs</a></p>
        </body>
    </html>
    """)

@app.get("/health")
async def health():
    """健康檢查"""
    try:
        supabase.table("api_keys").select("count").limit(1).execute()
        return {"status": "healthy", "database": "connected"}
    except:
        return {"status": "degraded", "database": "disconnected"}

@app.post("/v1/ocr/scan")
async def ocr_scan(
    file: UploadFile = File(...),
    region: str = "HK",
    api_key: dict = Depends(verify_api_key)
):
    """OCR 掃描 endpoint"""
    
    job_id = str(uuid.uuid4())
    start_time = time.time()
    temp_path = None
    
    try:
        if region not in ["HK", "CN", "MO"]:
            raise HTTPException(status_code=400, detail="Invalid region")
        
        file_content = await file.read()
        file_size = len(file_content)
        
        temp_path = f"/tmp/ocr_{job_id}.jpg"
        with open(temp_path, "wb") as f:
            f.write(file_content)
        
        print(f"📄 處理檔案: {file.filename} ({file_size} bytes) - Region: {region}")
        
        # 執行 OCR
        ocr = ocr_engines[region]
        result = ocr.ocr(temp_path)
        
        print(f"🔍 OCR 原始結果: {result}")
        
        # 解析結果 (加強防護)
        lines = []
        raw_text = []
        total_confidence = 0
        
        if result and len(result) > 0 and result[0]:
            for item in result[0]:
                try:
                    # 檢查結構
                    if not item or len(item) < 2:
                        continue
                    
                    text_info = item[1]
                    if not text_info or len(text_info) < 2:
                        continue
                    
                    text = str(text_info[0])
                    confidence = float(text_info[1])
                    
                    lines.append({"text": text, "confidence": round(confidence, 3)})
                    raw_text.append(text)
                    total_confidence += confidence
                    
                except Exception as parse_err:
                    print(f"⚠️ 解析單行失敗: {parse_err}, item: {item}")
                    continue
        
        total_lines = len(lines)
        confidence_avg = round(total_confidence / total_lines, 3) if total_lines > 0 else 0
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # 清理臨時檔案
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        # 儲存到 database
        try:
            supabase.table("ocr_jobs").insert({
                "id": job_id,
                "account_id": api_key["account_id"],
                "api_key_id": api_key["id"],
                "filename": file.filename,
                "file_size": file_size,
                "region": region,
                "status": "success",
                "total_lines": total_lines,
                "raw_text": "\n".join(raw_text) if raw_text else "",
                "structured_data": {"lines": lines},
                "confidence_avg": confidence_avg,
                "processing_time_ms": processing_time_ms
            }).execute()
        except Exception as db_err:
            print(f"⚠️ Database insert warning: {db_err}")
        
        print(f"✅ OCR 完成: {total_lines} 行, 平均信心度: {confidence_avg}")
        
        return {
            "status": "success",
            "job_id": job_id,
            "region": region,
            "lines": lines,
            "raw_text": "\n".join(raw_text) if raw_text else "",
            "total_lines": total_lines,
            "confidence_avg": confidence_avg,
            "processing_time_ms": processing_time_ms
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ OCR 錯誤: {e}")
        import traceback
        traceback.print_exc()
        
        # 清理臨時檔案
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
        
        raise HTTPException(status_code=500, detail=f"OCR failed: {str(e)}")

# ==================== Admin Endpoints ====================

class KeyGenerateRequest(BaseModel):
    account_id: str
    name: str

@app.post("/v1/admin/keys/generate")
async def generate_api_key(request: KeyGenerateRequest):
    """生成新 API Key"""
    try:
        import secrets
        raw_key = f"br{secrets.token_urlsafe(20)}"
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        key_prefix = raw_key[:10]
        
        result = supabase.table("api_keys").insert({
            "account_id": request.account_id,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "name": request.name,
            "is_active": True
        }).execute()
        
        key_id = result.data[0]["id"]
        print(f"✅ 生成新 API Key: {key_id}")
        
        return {
            "api_key": raw_key,
            "key_id": key_id,
            "account_id": request.account_id,
            "name": request.name
        }
    except Exception as e:
        print(f"❌ 生成 Key 錯誤: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 啟動 ====================

if __name__ == "__main__":
    import uvicorn
    print(f"\n🚀 啟動: http://0.0.0.0:8000\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")

