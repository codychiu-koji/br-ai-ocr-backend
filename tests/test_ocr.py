import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

client = TestClient(app)

@patch('ocr_service_v2.ocr.ocr')
def test_ocr_valid(mock_ocr, mock_supabase):
    mock_result = [[[(b&quot;box&quot;, (&quot;test text&quot;, 0.95))]]]
    mock_ocr.return_value = mock_result
    
    response = client.post(&quot;/v1/ocr/scan?region=HK&quot;,
                          headers={&quot;X-API-Key&quot;: &quot;br_test_key_123456789&quot;},
                          files={&quot;file&quot;: (&quot;test.jpg&quot;, b&quot;dummytest&quot;, &quot;image/jpeg&quot;)})
    assert response.status_code == 200
    data = response.json()
    assert data[&quot;status&quot;] == &quot;success&quot;
    assert &quot;test text&quot; in data[&quot;raw_text&quot;]

def test_ocr_invalid_region(mock_supabase):
    response = client.post(&quot;/v1/ocr/scan?region=INVALID&quot;,
                          headers={&quot;X-API-Key&quot;: &quot;br_test_key_123456789&quot;},
                          files={&quot;file&quot;: (&quot;test.jpg&quot;, b&quot;dummytest&quot;, &quot;image/jpeg&quot;)})
    assert response.status_code == 400
    assert &quot;Invalid region&quot; in response.json()[&quot;detail&quot;]

def test_ocr_missing_file(mock_supabase):
    response = client.post(&quot;/v1/ocr/scan?region=HK&quot;,
                          headers={&quot;X-API-Key&quot;: &quot;br_test_key_123456789&quot;})
    assert response.status_code == 422
