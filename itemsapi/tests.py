# tests.py
from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from .models import Item, Note, Attachment, Email, ComponentHistory

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
        response = self.client.get(self.base_url, {'hierarchical': 'false'})
        data = response.json()
        self.assertEqual(len(data), 2)
        parent_data = next(item for item in data if item['id'] == self.parent.id)
        self.assertEqual(parent_data['children'], [])

    # Parent Change & History Tests
    def test_change_parent_and_history(self):
        new_parent = Item.objects.create(name='New Parent')
        response = self.client.put(
            f'{self.base_url}/{self.child.id}/parent',
            {'new_parent_id': new_parent.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.child.refresh_from_db()
        self.assertEqual(self.child.parent, new_parent)
        
        history = ComponentHistory.objects.get()
        self.assertEqual(history.old_parent, self.parent)
        self.assertEqual(history.new_parent, new_parent)
        
        history_response = self.client.get(f'{self.base_url}/history')
        history_data = history_response.json()
        self.assertEqual(history_data[0]['old_parent_name'], 'Parent')
        self.assertEqual(history_data[0]['new_parent_name'], 'New Parent')

    def test_circular_parent_error(self):
        response = self.client.put(
            f'{self.base_url}/{self.parent.id}/parent',
            {'new_parent_id': self.child.id},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Circular dependency', response.json()['message'])

    # Deletion Tests
    def test_delete_item(self):
        response = self.client.delete(f'{self.base_url}/{self.parent.id}')
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Item.objects.count(), 1)

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
        