from django.test import TestCase
from ninja.testing import TestClient
from .models import Item, Note, Email
from .api import api 

class InventorySystemTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create single TestClient instance for all tests
        cls.client = TestClient(api)



    def setUp(self):
        super().setUp()
        # Create basic inventory structure
        self.storage = Item.objects.create(name="Storage Room")
        self.workbench = Item.objects.create(name="Workbench A")
        self.laptop = Item.objects.create(name="Customer Laptop", parent=self.workbench)

    def test_inventory_structure(self):
        """Test basic inventory organization"""
        self.assertEqual(self.laptop.parent, self.workbench)
        self.assertEqual(self.laptop.get_full_path(), "Workbench A/Customer Laptop")

    def test_repair_shop_workflow(self):
        """Test complete repair workflow"""
        # Customer brings laptop for repair
        laptop = Item.objects.create(
            name="Dell XPS 15",
            description="Customer laptop - overheating",
            parent=self.workbench
        )
        
        # Add repair documentation
        Note.objects.create(
            item=laptop,
            content="Initial diagnosis: Thermal paste needs replacement"
        )
        
        # Add replacement part from storage
        thermal_paste = Item.objects.create(
            name="Arctic MX-4",
            description="Thermal compound",
            parent=self.storage
        )
        
        # Move part to laptop repair
        response = self.client.put(f"/api/items/{thermal_paste.id}/move", 
            json={"new_parent_id": laptop.id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Add repair completion note
        Note.objects.create(
            item=laptop,
            content="Thermal paste replaced, temperatures normal"
        )
        
        # Verify history and documentation
        history = self.client.get(f"/api/items/{laptop.id}/history")
        self.assertEqual(len(history.json()), 1)
        
        response = self.client.get(f"/api/items/{laptop.id}")
        self.assertEqual(len(response.json()['notes']), 2)

    def test_component_lifecycle(self):
        """Test component creation, movement and deletion"""
        # Create component
        response = self.client.post(f"/api/items", json={
            'name': 'RAM Module',
            'description': '8GB DDR4',
            'parent_id': self.laptop.id
        })
        self.assertEqual(response.status_code, 201)
        ram_id = response.json()['id']
        
        # Move component
        response = self.client.put(f"/api/items/{ram_id}/move", 
            json={"new_parent_id": self.storage.id}
        )
        self.assertEqual(response.status_code, 200)
        
        # Verify history
        history = self.client.get(f"/api/items/{ram_id}/history")
        self.assertEqual(len(history.json()), 2)  # Created + Moved

    def test_search_functionality(self):
        """Test inventory search capabilities"""
        Item.objects.create(name="DDR4 RAM", description="8GB 2400MHz")
        Item.objects.create(name="DDR3 RAM", description="4GB 1600MHz")
        
        response = self.client.get(f"/api/items/search", params={"q": "DDR4"})
        self.assertEqual(len(response.json()), 1)

    def test_attachment_management(self):
        """Test component documentation features"""
        gpu = Item.objects.create(name="GPU")
        
        # Add various attachments
        Note.objects.create(item=gpu, content="Thermal paste replaced")
        Email.objects.create(
            item=gpu,
            subject="GPU RMA",
            body="RMA approved",
            from_address="support@vendor.com",
            received_at="2023-01-01T00:00:00Z"
        )
        
        response = self.client.get(f"/api/items/{gpu.id}")
        data = response.json()
        self.assertEqual(len(data['notes']), 1)
        self.assertEqual(len(data['emails']), 1)

    def test_tree_operations(self):
        """Test MPTT tree operations"""
        parent = Item.objects.create(name="Computer")
        child1 = Item.objects.create(name="CPU", parent=parent)
        child2 = Item.objects.create(name="GPU", parent=parent)
        
        # Test ancestors
        self.assertEqual(child1.get_ancestors().count(), 1)
        
        # Test siblings
        self.assertEqual(child1.get_siblings().count(), 1)
        
        # Test descendants
        self.assertEqual(parent.get_descendants().count(), 2)
        
        # Test tree structure
        self.assertEqual(child1.get_root(), parent)

    def test_validation(self):
        """Test data validation and constraints"""
        # Test circular reference prevention
        parent = Item.objects.create(name="Parent")
        child = Item.objects.create(name="Child", parent=parent)
        
        response = self.client.put(f"/api/items/{parent.id}/move", 
            json={"new_parent_id": child.id}
        )
        self.assertEqual(response.status_code, 400)



 