# tests.py
"""
This module contains test cases for the Items API, including tests for item creation, retrieval, 
update, hierarchical listing, parent change, deletion, and associated notes and attachments. 
It also includes tests for the ComponentHistory model to track changes in item parent relationships. 
The tests are implemented using Django's TestCase class and cover both successful and error scenarios.
"""
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .models import Item, Note, Attachment, Email, ComponentHistory
import logging
#logging.basicConfig(level=logging.DEBUG)
#logger = logging.getLogger('django.request')

#@override_settings(DEBUG=True)
class ItemAPITests(TestCase):
    def setUp(self):
        self.base_url = '/api/items'
        self.parent = Item.objects.create(name='Parent')
        self.child = Item.objects.create(name='Child', parent=self.parent)

    # Item Creation Tests
    def test_create_item_without_parent(self):
        response = self.client.post(
            self.base_url,
            {'name': 'Test Item'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Item.objects.count(), 3)
        self.assertEqual(Item.objects.get(name='Test Item').parent, None)

    def test_create_item_with_valid_parent(self):
        response = self.client.post(
            self.base_url,
            {'name': 'Test Child', 'parent_id': self.parent.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Item.objects.get(name='Test Child').parent, self.parent)

    def test_create_item_with_invalid_parent(self):
        response = self.client.post(
            self.base_url,
            {'name': 'Test', 'parent_id': 999},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Item.objects.count(), 2)

    # Item Retrieval Tests
    def test_get_item(self):
        response = self.client.get(f'{self.base_url}/{self.parent.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['name'], 'Parent')

    def test_get_nonexistent_item(self):
        response = self.client.get(f'{self.base_url}/999')
        self.assertEqual(response.status_code, 404)

    # Item Update Tests
    def test_full_update_item(self):
        response = self.client.put(
            f'{self.base_url}/{self.parent.id}',
            {'name': 'Updated Parent', 'description': 'New Desc'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.name, 'Updated Parent')
        self.assertEqual(self.parent.description, 'New Desc')

    def test_partial_update_item(self):
        response = self.client.patch(
            f'{self.base_url}/{self.parent.id}',
            {'description': 'Partial Update'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.parent.refresh_from_db()
        self.assertEqual(self.parent.description, 'Partial Update')

    # Hierarchical Listing Tests
    def test_list_items_hierarchical(self):
        response = self.client.get(self.base_url, {'hierarchical': 'true'})
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(len(data[0]['children']), 1)
        self.assertEqual(data[0]['children'][0]['name'], 'Child')

    def test_list_items_flat(self):
        """Verify flat list returns all items without nesting"""
    # Debug database state
        print("\nDatabase state:")
        print(f"Total items in DB: {Item.objects.count()}")
        for item in Item.objects.all():
            print(f"- Item {item.id}: {item.name} (parent: {item.parent_id})")

        response = self.client.get(f'{self.base_url}?hierarchical=false')
        data = response.json()
        print("\nAPI Response:")
        print(f"Items returned: {len(data)}")
        print("Raw response data:", data)

        for item in data:
            print(f"- Item {item['id']}: {item['name']} (parent: {item['parent_id']})")
            # Should return all items
            self.assertEqual(len(data), Item.objects.count())
        # Items should be in a flat list
        for item in data:
            self.assertEqual(item['children'], [])

    # Parent Change & History Tests
    def test_change_parent_and_history(self):
        new_parent = Item.objects.create(name='New Parent')    
        response = self.client.put(
            #f'{self.base_url}/{self.child.id}/parent?new_parent_id={new_parent.id}',
            f'{self.base_url}/{self.child.id}/parent',
            {'parent_id': new_parent.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)

        # Refresh child from database
        self.child.refresh_from_db()

        # First verify parent is not None
        self.assertIsNotNone(self.child.parent, "Child's parent should not be None")

        # Then verify parent is the new parent
        self.assertEqual(self.child.parent.id, new_parent.id)
        
        # Verify history
        history = ComponentHistory.objects.latest('changed_at')
        self.assertEqual(history.old_parent, self.parent)
        self.assertEqual(history.new_parent, new_parent)
        
        history_response = self.client.get(f'{self.base_url}/history')
        history_data = history_response.json()
        self.assertEqual(history_data[0]['old_parent_name'], 'Parent')
        self.assertEqual(history_data[0]['new_parent_name'], 'New Parent')

    def test_circular_parent_error(self):
        """Verify cannot make an item its own ancestor"""
        response = self.client.put(
            f'{self.base_url}/{self.parent.id}/parent',
            {'parent_id': self.child.id}, # Try to make item its own parent
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Circular dependency', response.json()['detail'])

    # Deletion Tests
    def test_delete_item(self):
        response = self.client.delete(f'{self.base_url}/{self.parent.id}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Item.objects.count(), 1)

    def test_mptt_tree_structure(self):
        root = Item.objects.create(name='Root')
        child1 = Item.objects.create(name='Child1', parent=root)
        child2 = Item.objects.create(name='Child2', parent=root)
        grandchild = Item.objects.create(name='GrandChild', parent=child1)
        
        # Test MPTT fields
        self.assertEqual(root.level, 0)
        self.assertEqual(child1.level, 1)
        self.assertEqual(grandchild.level, 2)
        
        # Test tree queries
        self.assertEqual(root.get_descendants().count(), 3)
        self.assertEqual(grandchild.get_ancestors().count(), 2)

    def test_mptt_move_node(self):
        root1 = Item.objects.create(name='Root1')
        root2 = Item.objects.create(name='Root2')
        child = Item.objects.create(name='Child', parent=root1)
        
        # Test moving node to different parent
        child.parent = root2
        child.save()
        
        self.assertEqual(child.parent, root2)
        self.assertEqual(root1.get_descendants().count(), 0)
        self.assertEqual(root2.get_descendants().count(), 1)
    def test_move_to_storage(self):
        response = self.client.put(
            f'{self.base_url}/{self.child.id}/parent',
            {'new_parent_id': None},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.child.refresh_from_db()
        self.assertIsNone(self.child.parent)

    def test_get_item_tree(self):
        root = Item.objects.create(name='Computer')
        motherboard = Item.objects.create(name='Motherboard', parent=root)
        cpu = Item.objects.create(name='CPU', parent=motherboard)
        
        response = self.client.get(f'{self.base_url}/{root.id}/tree')
        data = response.json()
        
        self.assertEqual(len(data), 3)  # Root + 2 descendants
        names = [item['name'] for item in data]
        self.assertEqual(names, ['Computer', 'Motherboard', 'CPU'])

    def test_get_breadcrumb(self):
        root = Item.objects.create(name='Computer')
        motherboard = Item.objects.create(name='Motherboard', parent=root)
        cpu = Item.objects.create(name='CPU', parent=motherboard)
        
        response = self.client.get(f'{self.base_url}/{cpu.id}/breadcrumb')
        data = response.json()
        
        self.assertEqual(len(data), 3)
        names = [item['name'] for item in data]
        self.assertEqual(names, ['Computer', 'Motherboard', 'CPU'])
    def test_search_with_descendants(self):
        # Create test data
        root = Item.objects.create(name='Computer')
        motherboard = Item.objects.create(name='Motherboard', parent=root)
        cpu = Item.objects.create(name='CPU', parent=motherboard)
        
        print("\nTree Structure:")
        print(f"Root: {root.name} (id:{root.id}, tree_id:{root.tree_id}, lft:{root.lft}, rght:{root.rght})")
        print(f"Motherboard: {motherboard.name} (id:{motherboard.id}, tree_id:{motherboard.tree_id}, lft:{motherboard.lft}, rght:{motherboard.rght})")
        print(f"CPU: {cpu.name} (id:{cpu.id}, tree_id:{cpu.tree_id}, lft:{cpu.lft}, rght:{cpu.rght})")

        # Debug database state
        print("\nAll Items in DB:")
        for item in Item.objects.all():
            print(f"- {item.name}: parent={item.parent.name if item.parent else 'None'}, "
                  f"tree_id={item.tree_id}, lft={item.lft}, rght={item.rght}")

        response = self.client.get(f'{self.base_url}/search?name=mother')
        data = response.json()
        
        print("\nSearch Response:")
        print(f"Results count: {len(data)}")
        print("Found items:")
        for item in data:
            print(f"- {item['name']} (parent_id: {item['parent_id']})")

        self.assertEqual(len(data), 2)  # Should return Motherboard and CPU
        names = [item['name'] for item in data]
        self.assertIn('Motherboard', names)
        self.assertIn('CPU', names)
class NoteAPITests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item')
        self.note_url = f'/api/items/{self.item.id}/notes'

    def test_create_note(self):
        response = self.client.post(
            self.note_url,
            {'content': 'Test Note'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Note.objects.count(), 1)
        self.assertEqual(Note.objects.first().content, 'Test Note')

    def test_delete_note(self):
        note = Note.objects.create(item=self.item, content='Test')
        response = self.client.delete(f'{self.note_url}/{note.id}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Note.objects.count(), 0)

class AttachmentAPITests(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name='Test Item')
        self.attachment_url = f'/api/items/{self.item.id}/attachments'

    def test_create_attachment(self):
        test_file = SimpleUploadedFile('test.txt', b'content', 'text/plain')
        response = self.client.post(
            self.attachment_url,
            {'file': test_file},
            format='multipart'
        )
        self.assertEqual(response.status_code, 201)
        attachment = Attachment.objects.first()
        self.assertTrue(attachment.file.name.startswith('attachments/test'))
        self.assertEqual(attachment.type, 'text/plain')

class ComponentHistoryTests(TestCase):
    def test_history_retrieval(self):
        item = Item.objects.create(name='Item')
        ComponentHistory.objects.create(item=item, old_parent=None, new_parent=None)
        response = self.client.get('/api/items/history')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)
        self.assertEqual(response.json()[0]['item_name'], 'Item')
        