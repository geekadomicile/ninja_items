from django.test import TestCase
from django.core.management import call_command
from django.utils import timezone
from django.db import transaction
from ninja.testing import TestClient

from .models import Item, Note, Email, File, CodeIdentifier, ComponentHistory
from .api import api

class InventorySystemTests(TestCase):
    """
    Test suite for inventory management system
    Covers: MPTT operations, component lifecycle, documentation features
    """
    fixtures = ['initial_data.json']
    
    @classmethod
    def setUpTestData(cls):
        """Rebuild MPTT tree and setup shared test data"""
        from .models import Item
        Item.objects.rebuild()
        super().setUpTestData()
        cls.client = TestClient(api)

    def setUp(self):
        """Initialize test data"""
        with transaction.atomic():
            # Check if items already exist from fixtures
            try:
                self.storage = Item.objects.get(name="Storage Room")
            except Item.DoesNotExist:
                self.storage = Item.objects.create(name="Storage Room")
            
            try:
                self.workbench = Item.objects.get(name="Workbench A")
            except Item.DoesNotExist:
                self.workbench = Item.objects.create(name="Workbench A")
            
            try:
                self.laptop = Item.objects.get(name="Customer Laptop")
            except Item.DoesNotExist:
                self.laptop = Item.objects.create(
                    name="Customer Laptop", 
                    parent=self.workbench,
                    description="Test laptop"
                )

    def test_inventory_structure(self):
        """Verify MPTT tree structure and path generation"""
        self.assertEqual(self.laptop.parent, self.workbench)
        self.assertEqual(self.laptop.get_full_path(), "Workbench A/Customer Laptop")
        
        # Test tree relationships
        self.assertEqual(self.laptop.get_root(), self.workbench)
        self.assertTrue(self.laptop in self.workbench.get_descendants())

    def test_repair_shop_workflow(self):
        """Test complete repair workflow with documentation"""
        # Create repair case
        laptop = Item.objects.create(
            name="Dell XPS 15",
            description="Customer laptop - overheating",
            parent=self.workbench
        )
        
        # Test documentation
        note = Note.objects.create(
            item=laptop,
            content="Initial diagnosis: Thermal paste needs replacement"
        )
        
        # Test part movement
        thermal_paste = Item.objects.create(
            name="Arctic MX-4",
            description="Thermal compound",
            parent=self.storage
        )
        
        response = self.client.put(
            f"/api/items/{thermal_paste.id}/move",
            json={"new_parent_id": laptop.id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify documentation
        Note.objects.create(
            item=laptop,
            content="Thermal paste replaced, temperatures normal"
        )
        
        # Verify history tracking
        history = self.client.get(f"/api/items/{laptop.id}/history")
        self.assertGreaterEqual(len(history.json()), 1)
        
        # Test full item data retrieval
        response = self.client.get(f"/api/items/{laptop.id}")
        data = response.json()
        self.assertEqual(len(data['notes']), 2)
        self.assertIn('thermal paste', data['notes'][0]['content'].lower())

    def test_component_lifecycle(self):
        """Test component CRUD operations and movement tracking"""
        # Create component
        payload = {
            'name': 'RAM Module',
            'description': '8GB DDR4',
            'parent_id': self.laptop.id,
            'qr_code': 'RAM003'
        }
       
        response = self.client.post(
            "/api/items",
            json=payload
        )
        if response.status_code != 201:
            print(f"Error creating item: {response.content}")
        self.assertEqual(response.status_code, 201)
        ram_id = response.json()['id']
        
        # Test movement
        response = self.client.put(
            f"/api/items/{ram_id}/move",
            json={"new_parent_id": self.storage.id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify history
        history = self.client.get(f"/api/items/{ram_id}/history")
        self.assertGreaterEqual(len(history.json()), 1)

    def test_search_functionality(self):
        """Test search capabilities across different fields"""
        # Create test items
        Item.objects.create(
            name="DDR4 RAM",
            description="8GB 2400MHz",
            qr_code="RAM001"
        )
        Item.objects.create(
            name="DDR3 RAM",
            description="4GB 1600MHz",
            qr_code="RAM002"
        )
        
        # Test name search
        response = self.client.get("/api/items/search", params={"q": "DDR4"})
        self.assertEqual(len(response.json()), 1)
        
        # Test description search
        response = self.client.get("/api/items/search", params={"q": "1600MHz"})
        self.assertEqual(len(response.json()), 1)
        
        # Test QR code search
        response = self.client.get("/api/items/search", params={"q": "RAM001"})
        self.assertEqual(len(response.json()), 1)

    def test_attachment_management(self):
        """Test all types of attachments and documentation"""
        gpu = Item.objects.create(name="GPU")
        
        # Test notes
        Note.objects.create(item=gpu, content="Thermal paste replaced")
        
        # Test emails
        Email.objects.create(
            item=gpu,
            subject="GPU RMA",
            body="RMA approved",
            from_address="support@vendor.com",
            received_at=timezone.now()
        )
        
        # Test files
        File.objects.create(
            item=gpu,
            file="test.pdf",
            file_type="application/pdf"
        )
        
        # Test codes
        CodeIdentifier.objects.create(
            item=gpu,
            code="GPU123",
            source="manufacturer"
        )
        
        # Verify all attachments
        response = self.client.get(f"/api/items/{gpu.id}")
        data = response.json()
        self.assertEqual(len(data['notes']), 1)
        self.assertEqual(len(data['emails']), 1)
        self.assertEqual(len(data['files']), 1)
        self.assertEqual(len(data['codes']), 1)

    def test_tree_operations(self):
        """Test MPTT specific operations and constraints"""
        # Create test tree
        computer = Item.objects.create(name="Computer")
        cpu = Item.objects.create(name="CPU", parent=computer)
        gpu = Item.objects.create(name="GPU", parent=computer)
        
        # Test tree traversal
        self.assertEqual(cpu.get_ancestors().count(), 1)
        self.assertEqual(cpu.get_siblings().count(), 1)
        self.assertEqual(computer.get_descendants().count(), 2)
        
        # Test root identification
        self.assertEqual(cpu.get_root(), computer)
        
        # Test level information
        self.assertEqual(computer.level, 0)
        self.assertEqual(cpu.level, 1)

    def test_validation(self):
        """Test data validation and business rules"""
        # Test circular reference prevention
        parent = Item.objects.create(name="Parent")
        child = Item.objects.create(name="Child", parent=parent)
        
        response = self.client.put(
            f"/api/items/{parent.id}/move",
            json={"new_parent_id": child.id}
        )
        self.assertEqual(response.status_code, 400)

    def tearDown(self):
        """Clean up after each test"""
        File.objects.all().delete()
        Item.objects.all().delete()
        super().tearDown()
