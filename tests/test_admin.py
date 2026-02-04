import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

client = TestClient(app)

@patch('ocr_service_v2.supabase.table')
def test_generate_key(mock_table, mock_supabase):
    mock_insert = mock_table.return_value.insert.return_value.execute
    mock_insert.return_value = {'data': [{'id': 'new_key_id'}]}
    
    response = client.post(&quot;/v1/admin/keys/generate&quot;,
                          json={&quot;account_id&quot;: &quot;test_acc&quot;, &quot;name&quot;: &quot;Test Key&quot;})
    assert response.status_code == 200
    data = response.json()
    assert data[&quot;api_key&quot;].startswith(&quot;br&quot;)
    assert data[&quot;account_id&quot;] == &quot;test_acc&quot;
