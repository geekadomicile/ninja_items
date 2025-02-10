from django.test import TestCase
from ninja.testing import TestClient
from .api import api
from .models import Item

class DebugInventoryTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = TestClient(api)

    def test_get_items(self):
        """Test basic GET items endpoint"""
        Item.objects.create(name="Test Item")
        response = self.client.get("/api/items")
        self.assertEqual(response.status_code, 200)
    
    def test_post_item(self):
        """Test POST endpoint with debug output"""
        payload = {
            "name": "Test Item",
            "description": "Test",
            "qr_code": "string",
            "parent_id": None  # Matching schema's Optional[int] = None
        }
        print(f"Sending payload: {payload}")
        response = self.client.post(
            "/api/items",
            payload,
            content_type="application/json"
        )
        print(f"Response: {response.content}")
        self.assertEqual(response.status_code, 201)