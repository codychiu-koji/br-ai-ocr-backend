# BR AI OCR API v2.0 - 完整 API 文檔

## 認證 (Authentication)
所有保護 endpoints 需要 `X-API-Key` header。

### 如何獲取 API Key
使用 `POST /v1/admin/keys/generate` 生成。

**範例**:
```bash
curl -X POST http://localhost:8000/v1/admin/keys/generate \\
  -H &quot;Content-Type: application/json&quot; \\
  -d '{
    &quot;account_id&quot;: &quot;acc_123&quot;,
    &quot;name&quot;: &quot;Test App&quot;
  }'
```

**回應**:
```json
{
  &quot;api_key&quot;: &quot;brABC123def456ghi789&quot;,
  &quot;key_id&quot;: &quot;uuid&quot;,
  &quot;account_id&quot;: &quot;acc_123&quot;,
  &quot;name&quot;: &quot;Test App&quot;
}
```

使用 key: `X-API-Key: brABC123def456ghi789`

## Endpoints

### GET /health
**健康檢查**

**Curl**:
```bash
curl http://localhost:8000/health
```

**成功 (200)**:
```json
{&quot;status&quot;: &quot;healthy&quot;, &quot;database&quot;: &quot;connected&quot;}
```

**降級**:
```json
{&quot;status&quot;: &quot;degraded&quot;, &quot;database&quot;: &quot;disconnected&quot;}
```

### POST /v1/ocr/scan
**OCR 掃描圖片文字**

**參數**:
- `file` (form-data, jpg/png): 圖片檔案
- `region` (query): HK/CN/MO (預設 HK)
- `X-API-Key` (header): API 金鑰

**Curl 完整範例**:
```bash
curl -X POST &quot;http://localhost:8000/v1/ocr/scan?region=HK&quot; \\
  -H &quot;X-API-Key: brABC123def456ghi789&quot; \\
  -F &quot;file=@image.jpg&quot;
```

**成功 (200)**:
```json
{
  &quot;status&quot;: &quot;success&quot;,
  &quot;job_id&quot;: &quot;uuid&quot;,
  &quot;region&quot;: &quot;HK&quot;,
  &quot;lines&quot;: [{&quot;text&quot;: &quot;香港銀行&quot;, &quot;confidence&quot;: 0.95}],
  &quot;raw_text&quot;: &quot;香港銀行\n123街&quot;,
  &quot;total_lines&quot;: 2,
  &quot;confidence_avg&quot;: 0.93,
  &quot;processing_time_ms&quot;: 1200
}
```

**錯誤**:
- **400 Invalid region**: region 不在 HK/CN/MO
- **401 Invalid API key**: Key 無效或停用
- **422 Validation error**: 缺少 file
- **500 Server error**: OCR 失敗或 DB 錯誤

### POST /v1/admin/keys/generate
**生成新 API Key**

**Body**:
```json
{&quot;account_id&quot;: &quot;acc_123&quot;, &quot;name&quot;: &quot;App Key&quot;}
```

**Curl**:
```bash
curl -X POST http://localhost:8000/v1/admin/keys/generate \\
  -H &quot;Content-Type: application/json&quot; \\
  -d '&quot;{...}&quot;'
```

**錯誤代碼總結**:
| Code | 原因 |
|------|------|
| 400 | Invalid region |
| 401 | Invalid/missing API key |
| 422 | Validation failed (missing file/body) |
| 500 | Internal error (OCR/DB)
