import pytest
from fastapi.testclient import TestClient
from ocr_service_v2 import app

client = TestClient(app)

def test_valid_api_key(mock_supabase):
    response = client.post(&quot;/v1/ocr/scan&quot;, 
                          headers={&quot;X-API-Key&quot;: &quot;br_test_key_123456789&quot;},
                          files={&quot;file&quot;: (&quot;test.jpg&quot;, b&quot;dummytest&quot;, &quot;image/jpeg&quot;)})
    assert response.status_code == 500  # OCR will fail but auth passes

def test_invalid_api_key(mock_supabase):
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = {'data': []}
    response = client.post(&quot;/v1/ocr/scan&quot;, 
                          headers={&quot;X-API-Key&quot;: &quot;invalid&quot;},
                          files={&quot;file&quot;: (&quot;test.jpg&quot;, b&quot;dummytest&quot;, &quot;image/jpeg&quot;)})
    assert response.status_code == 401
    assert &quot;Invalid API key&quot; in response.json()[&quot;detail&quot;]

def test_missing_api_key(mock_supabase):
    response = client.post(&quot;/v1/ocr/scan&quot;, 
                          files={&quot;file&quot;: (&quot;test.jpg&quot;, b&quot;dummytest&quot;, &quot;image/jpeg&quot;)})
    assert response.status_code == 422  # FastAPI validation for header
