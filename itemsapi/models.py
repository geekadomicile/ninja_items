from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class Item(MPTTModel):
    name = models.CharField(max_length=255, db_index=True)
    qr_code = models.CharField(max_length=255, db_index=True, blank=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    def get_full_path(self):
        """Returns complete path from root to this item"""
        return '/'.join([item.name for item in self.get_ancestors(include_self=True)])
    @classmethod
    def get_prefetch_fields(cls):
        """Returns list of related fields to prefetch for better performance"""
        return [
            'children',
            'notes',
            'files',
            'emails',
            'codes',
            'history'
        ]
    def get_all_attachments(self):
        """Returns all types of attachments for this item and descendants"""
        item_ids = self.get_descendants(include_self=True).values_list('id', flat=True)
        return {
            'notes': Note.objects.filter(item_id__in=item_ids),
            'files': File.objects.filter(item_id__in=item_ids),
            'emails': Email.objects.filter(item_id__in=item_ids),
            'codes': CodeIdentifier.objects.filter(item_id__in=item_ids)
        }
class CodeIdentifier(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='codes')
    code = models.CharField(max_length=100, db_index=True)
    source = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class Note(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class File(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='attachments/')
    file_type = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

class Email(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='emails')
    subject = models.CharField(max_length=255)
    body = models.TextField()
    from_address = models.EmailField()
    received_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class ComponentHistory(models.Model):
    CREATED = 'created'
    MOVED = 'moved'
    DELETED = 'deleted'
    ACTION_CHOICES = [
        (CREATED, 'Created'),
        (MOVED, 'Moved'),
        (DELETED, 'Deleted'),
    ]
    
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='history')
    old_parent = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='old_parent_history')
    new_parent = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, related_name='new_parent_history')
    action_type = models.CharField(max_length=20, choices=ACTION_CHOICES)
    changed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-changed_at']