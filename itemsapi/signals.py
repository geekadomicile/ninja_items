from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Item, ComponentHistory

@receiver(post_save, sender=Item)
def track_item_changes(sender, instance, created, **kwargs):
    action_type = ComponentHistory.CREATED if created else ComponentHistory.MOVED
    ComponentHistory.objects.create(
        item=instance,
        old_parent=getattr(instance, '_previous_parent', None),
        new_parent=instance.parent,
        action_type=action_type
    )

@receiver(pre_delete, sender=Item)
def track_item_deletion(sender, instance, **kwargs):
    ComponentHistory.objects.create(
        item=instance,
        old_parent=instance.parent,
        new_parent=None,
        action_type=ComponentHistory.DELETED
    )
