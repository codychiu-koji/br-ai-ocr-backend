# BR AI OCR Backend v2.0

## 專案描述
FastAPI 後端服務，使用 PaddleOCR 進行中文 OCR 識別，支援香港(HK)、中國(CN)、澳門(MO)地區。整合 Supabase 資料庫記錄 job 與 API key 管理。

## 特色
- ✅ PaddleOCR 多地區支援 (chinese_cht/ch)
- ✅ API Key 認證 (SHA256 hash)
- ✅ 自動記錄所有 OCR jobs 到 Supabase
- ✅ 健康檢查與監控
- ✅ Docker 部署準備
- ✅ Pytest 測試套件
- ✅ Railway CI/CD

## 技術棧
- **Backend**: FastAPI 0.115+
- **OCR**: PaddleOCR + PaddlePaddle
- **DB**: Supabase (PostgreSQL)
- **部署**: Docker, Railway
- **測試**: Pytest, httpx

## 快速啟動 (Local)

1. **複製環境變數**:
   ```bash
   cp .env.example .env
   # 填入 Supabase URL & Service Key
   ```

2. **安裝依賴**:
   ```bash
   pip install -r requirements.txt
   ```

3. **啟動服務**:
   ```bash
   python ocr_service_v2.py
   ```
   訪問: http://localhost:8000/docs

## API Endpoints
詳見 [API_DOCS.md](./API_DOCS.md)

## 部署到 Railway
1. Push 到 GitHub main
2. CI/CD 自動部署 (需 RAILWAY_TOKEN secret)
3. 或手動: `railway up`

## 測試
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

## 監控
```bash
python monitoring_agent.py
```

## 環境變數
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_SERVICE_KEY`: Service role key

## License
MIT
