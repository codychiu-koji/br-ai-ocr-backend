import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from ocr_service_v2 import app  # Import the app

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def mock_supabase():
    mock = Mock()
    mock.table.return_value.select.return_value.eq.return_value.execute.return_value = {'data': [{'id': 'test_key', 'account_id': 'test_acc', 'is_active': True}]}
    mock.table.return_value.update.return_value.eq.return_value.execute.return_value = {'data': []}
    mock.table.return_value.insert.return_value.execute.return_value = {'data': [{'id': 'new_key'}]}
    with patch('ocr_service_v2.supabase', mock):
        yield mock

@pytest.fixture
def valid_api_key():
    return &quot;br_test_key_123456789&quot;

@pytest.fixture
def test_image_path():
    # Create a dummy image for testing
    import io
    from PIL import Image
    img = Image.new('RGB', (100, 100), color='red')
    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='JPEG')
    img_byte_arr.seek(0)
    return img_byte_arr
