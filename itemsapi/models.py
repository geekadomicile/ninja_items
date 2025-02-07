from django.db import models
from mptt.models import MPTTModel, TreeForeignKey

class Item(MPTTModel):
    name = models.CharField(max_length=255, db_index=True)
    qr_code = models.CharField(max_length=255, db_index=True, blank=True)
    description = models.TextField(blank=True, null=True)
    parent = TreeForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    created_at = models.DateTimeField(auto_now_add=True)

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    @classmethod
    def get_prefetch_fields(cls):
        return ['notes', 'attachments', 'emails']