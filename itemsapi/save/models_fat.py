# models.py
from django.db import models
from django.core.exceptions import ValidationError
from mptt.models import MPTTModel, TreeForeignKey

class Item(MPTTModel):
    id = models.AutoField(primary_key=True)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    name = models.CharField(max_length=255)
    qr_code = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ['name']
  
    def get_full_path(self):
        return '/'.join([ancestor.name for ancestor in self.get_ancestors(include_self=True)])
    
    @classmethod
    def get_prefetch_fields(cls):
        return [
            'children',
            'notes',
            'attachments',
            'emails',
            'history'
        ]
    def get_hierarchy_path(self):
        """Returns path like 'Computer/Motherboard/CPU'"""
        return '/'.join([item.name for item in self.get_ancestors(include_self=True)])
    
    def get_descendants_count(self):
        """Returns count of all nested components"""
        return self.get_descendant_count()

    def get_siblings_list(self):
        """Returns all components at same level"""
        return self.get_siblings(include_self=False)

class ComponentHistory(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='history')#@todo: check if this is correct(maybe we shoulduse .SET_NULL or .CASCADE)
    old_parent = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='old_parent_history')
    new_parent = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='new_parent_history')
    changed_at = models.DateTimeField(auto_now_add=True)

class Note(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, related_name='notes', null=True)
    content = models.TextField()
    author = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

class Attachment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, related_name='attachments', null=True)
    file = models.FileField(upload_to='attachments/')
    type = models.CharField(max_length=50)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Email(models.Model):
    item = models.ForeignKey(Item, on_delete=models.SET_NULL, related_name='emails', null=True)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    from_address = models.EmailField()
    received_at = models.DateTimeField()
    processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)