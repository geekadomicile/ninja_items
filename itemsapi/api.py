from ninja import NinjaAPI, Schema, Router, UploadedFile, File
from ninja.errors import HttpError
from django.core.exceptions import ValidationError
from typing import List, Any
from .models import Item, Note, Attachment, Email, ComponentHistory


api = NinjaAPI()
router = Router()

# Base schemas
class NoteSchema(Schema):
    id: int
    content: str
    created_at: Any

class AttachmentSchema(Schema):
    id: int
    file: str
    type: str
    uploaded_at: Any

class EmailSchema(Schema):
    id: int
    subject: str
    content: str
    created_at: Any

class ComponentHistorySchema(Schema):
    id: int
    item: int | None
    old_parent: int | None
    new_parent: int | None
    changed_at: Any

    @staticmethod
    def resolve_item(obj):
        return obj.item.id if obj.item else None

    @staticmethod
    def resolve_old_parent(obj):
        return obj.old_parent.id if obj.old_parent else None

    @staticmethod
    def resolve_new_parent(obj):
        return obj.new_parent.id if obj.new_parent else None

# Input schemas
class ItemIn(Schema):
    name: str
    description: str | None = None
    parent_id: int | None = None

class NoteIn(Schema):
    content: str

class EmailIn(Schema):
    subject: str
    content: str

# Output schema with nested relationships
class ItemOut(Schema):
    id: int
    name: str
    description: str | None
    created_at: Any
    parent_id: int | None
    children: List["ItemOut"] = []
    notes: List[NoteSchema] = []
    attachments: List[AttachmentSchema] = []
    emails: List[EmailSchema] = []
    
    @staticmethod
    def resolve_children(obj):
        if getattr(obj, '_flat_view', False):
            return []
            
        if not hasattr(obj, 'children') or obj.id in getattr(obj, '_processed_ids', set()):
            return []
        obj._processed_ids = getattr(obj, '_processed_ids', set()) | {obj.id}
        return obj.children.all()
    
    @staticmethod
    def resolve_notes(obj):
        return obj.notes.all() if hasattr(obj, 'notes') else []
        
    @staticmethod
    def resolve_attachments(obj):
        return obj.attachments.all() if hasattr(obj, 'attachments') else []
        
    @staticmethod
    def resolve_emails(obj):
        return obj.emails.all() if hasattr(obj, 'emails') else []

# Item endpoints
@router.get('/items', response=List[ItemOut])
def list_items(request, hierarchical: bool = True):
    queryset = Item.objects.select_related('parent')
    
    if hierarchical:
        queryset = queryset.filter(parent__isnull=True)
        return queryset.prefetch_related(
            'children',
            'notes',
            'attachments',
            'emails'
        )
    else:
        items = queryset.prefetch_related(
            'notes',
            'attachments',
            'emails'
        )
        for item in items:
            item._flat_view = True
        return items

@router.get('/items/history', response=List[ComponentHistorySchema])
def get_component_history(request):
    return ComponentHistory.objects.all().order_by('-changed_at')

@router.post('/items', response=ItemOut)
def create_item(request, data: ItemIn):
    if data.parent_id:
        try:
            Item.objects.get(id=data.parent_id)
        except Item.DoesNotExist:
            raise HttpError(404, "Parent item not found")
    item = Item.objects.create(**data.dict())
    return item

@router.get('/items/{item_id}', response=ItemOut)
def get_item(request, item_id: int):
    """Get item with complete component hierarchy"""
    item = Item.objects.filter(id=item_id).prefetch_related(
        *Item.get_prefetch_fields()
    ).first()
    if not item:
        raise HttpError(404, "Item not found")
    return item

@router.put('/items/{item_id}', response=ItemOut)
def update_item(request, item_id: int, data: ItemIn):
    try:
        item = Item.objects.get(id=item_id)
        for attr, value in data.dict().items():
            setattr(item, attr, value)
        item.save()
        return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

@router.patch('/items/{item_id}', response=ItemOut)
def partial_update_item(request, item_id: int, data: ItemIn):
    try:
        item = Item.objects.get(id=item_id)
        for attr, value in data.dict(exclude_unset=True).items():
            setattr(item, attr, value)
        item.save()
        return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    
@router.get('/items/search', response=List[ItemOut])
def search_items(request, qr_code: str = None, name: str = None, description: str = None):
    """
    Search items by various fields
    Returns flat list of matching items with their relationships
    """
    queryset = Item.objects
    
    if qr_code:
        queryset = queryset.filter(qr_code=qr_code)
    if name:
        queryset = queryset.filter(name__icontains=name)
    if description:
        queryset = queryset.filter(description__icontains=description)
        
    return queryset.prefetch_related(
        *Item.get_prefetch_fields()
    )

@router.put('/items/{item_id}/parent', response=ItemOut)
def change_parent(request, item_id: int, new_parent_id: int | None = None):
    try:
        item = Item.objects.get(id=item_id)
        old_parent = item.parent
        
        if new_parent_id:
            new_parent = Item.objects.get(id=new_parent_id)
            if new_parent == item:
                raise HttpError(400, "Cannot make item its own parent")
        else:
            new_parent = None
            
        ComponentHistory.objects.create(
            item=item,
            old_parent=old_parent,
            new_parent=new_parent
        )
        
        item.parent = new_parent
        item.full_clean()  # Runs validation including circular dependency check
        item.save()
        return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, str(e))


@router.delete('/items/{item_id}')
def delete_item(request, item_id: int):
    try:
        item = Item.objects.get(id=item_id)
        item.delete()
        return {"success": True}
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

# Note endpoints
@router.post('/items/{item_id}/notes', response=NoteSchema)
def create_note(request, item_id: int, data: NoteIn):
    try:
        item = Item.objects.get(id=item_id)
        return Note.objects.create(item=item, **data.dict())
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

@router.delete('/items/{item_id}/notes/{note_id}')
def delete_note(request, item_id: int, note_id: int):
    try:
        note = Note.objects.get(item_id=item_id, id=note_id)
        note.delete()
        return {"success": True}
    except Note.DoesNotExist:
        raise HttpError(404, "Note not found")

# Email endpoints
@router.post('/items/{item_id}/emails', response=EmailSchema)
def create_email(request, item_id: int, data: EmailIn):
    try:
        item = Item.objects.get(id=item_id)
        return Email.objects.create(item=item, **data.dict())
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

@router.delete('/items/{item_id}/emails/{email_id}')
def delete_email(request, item_id: int, email_id: int):
    try:
        email = Email.objects.get(item_id=item_id, id=email_id)
        email.delete()
        return {"success": True}
    except Email.DoesNotExist:
        raise HttpError(404, "Email not found")

# Attachment endpoints
@router.post('/items/{item_id}/attachments', response=AttachmentSchema)
def create_attachment(request, item_id: int, file: UploadedFile = File(...)):
    try:
        item = Item.objects.get(id=item_id)
        return Attachment.objects.create(
            item=item,
            file=file,
            type=file.content_type
        )
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

@router.delete('/items/{item_id}/attachments/{attachment_id}')
def delete_attachment(request, item_id: int, attachment_id: int):
    try:
        attachment = Attachment.objects.get(item_id=item_id, id=attachment_id)
        attachment.delete()
        return {"success": True}
    except Attachment.DoesNotExist:
        raise HttpError(404, "Attachment not found")

api.add_router('', router)
