from ninja import NinjaAPI, Schema, Router, UploadedFile, File
from ninja.errors import HttpError
from django.core.exceptions import ValidationError
from django.db import transaction
from typing import List, Any, Dict
from datetime import datetime
from .models import Item, Note, Attachment, Email, ComponentHistory


api = NinjaAPI()
router = Router()

# Error response schemas
class ErrorResponse(Schema):
    detail: str

class ValidationErrorResponse(Schema):
    detail: Dict[str, List[str]]

# Base response schemas
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
    item_name: str | None  # Add this to store item name
    old_parent_name: str | None  # Add this to store old parent name
    new_parent_name: str | None  # Add this to store new parent name

    @staticmethod
    def resolve_item(obj):
        return obj.item.id if obj.item else None
    
    @staticmethod
    def resolve_old_parent(obj):
        return obj.old_parent.id if obj.old_parent else None

    @staticmethod
    def resolve_new_parent(obj):
        return obj.new_parent.id if obj.new_parent else None
    @staticmethod
    def resolve_item_name(obj):
        return obj.item.name if obj.item else "Deleted Item"

    @staticmethod
    def resolve_old_parent_name(obj):
        return obj.old_parent.name if obj.old_parent else "Storage"

    @staticmethod
    def resolve_new_parent_name(obj):
        return obj.new_parent.name if obj.new_parent else "Storage"
    
# Input/Output schemas
class ItemCreate(Schema):
    name: str
    description: str | None = None
    parent_id: int | None = None

class ItemUpdate(Schema):
    name: str | None = None
    description: str | None = None
    parent_id: int | None = None

class NoteCreate(Schema):
    content: str
    author: str = "System"  # Default author if not provided

class EmailCreate(Schema):
    subject: str
    content: str

# Response schemas
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
        if not hasattr(obj, '_processed_ids'):
            obj._processed_ids = set()
        if obj.id in obj._processed_ids:
            return []
        obj._processed_ids.add(obj.id)
        return getattr(obj, 'children', [])
    
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
@router.get('/items', response={200: List[ItemOut], 500: ErrorResponse})
def list_items(request, hierarchical: bool = True):
    """
    List items either in hierarchical (tree) or flat structure
    """
    try:
        queryset = Item.objects.select_related('parent')
        
        if hierarchical:
            # Return only root items with their full tree
            items = queryset.filter(parent__isnull=True).prefetch_related(
                'children',
                'notes',
                'attachments',
                'emails'
            )
        else:
            # Return all items in a flat list
            items = queryset.all().prefetch_related(
                'notes',
                'attachments',
                'emails'
            )
            # Prevent children from being included in flat view
            #for item in items:
            #    setattr(item, '_flat_view', True)
            #    setattr(item, 'children', [])
        
        return items
    except Exception as e:
        raise HttpError(500, str(e))

@router.get('/items/history', response=List[ComponentHistorySchema])
def get_component_history(request):
    return ComponentHistory.objects.all().order_by('-changed_at')

@router.post('/items', response={201: ItemOut, 404: ErrorResponse, 400: ValidationErrorResponse})
def create_item(request, data: ItemCreate):
    try:
        with transaction.atomic():
            if data.parent_id:
                try:
                    parent = Item.objects.get(id=data.parent_id)
                except Item.DoesNotExist:
                    raise HttpError(404, "Parent item not found")
            
            item = Item(**data.dict())
            item.full_clean()  # Validate before saving
            item.save()
            return 201, item
    except ValidationError as e:
        raise HttpError(400, dict(e))

@router.get('/items/{item_id}', response=ItemOut)
def get_item(request, item_id: int):
    item = Item.objects.filter(id=item_id).select_related('parent').prefetch_related(
        *Item.get_prefetch_fields()
    ).first()
    if not item:
        raise HttpError(404, "Item not found")
    return item

@router.put('/items/{item_id}', response={200: ItemOut, 404: ErrorResponse, 400: ValidationErrorResponse})
def update_item(request, item_id: int, data: ItemUpdate):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            
            if data.parent_id is not None:
                try:
                    parent = Item.objects.get(id=data.parent_id)
                    if parent == item:
                        raise ValidationError("Item cannot be its own parent")
                except Item.DoesNotExist:
                    raise HttpError(404, "Parent item not found")
            
            for attr, value in data.dict(exclude_unset=True).items():
                setattr(item, attr, value)
                
            item.full_clean()
            item.save()
            return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))

@router.patch('/items/{item_id}', response={200: ItemOut, 404: ErrorResponse, 400: ValidationErrorResponse})
def partial_update_item(request, item_id: int, data: ItemUpdate):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            
            if data.parent_id is not None:
                try:
                    parent = Item.objects.get(id=data.parent_id)
                    if parent == item:
                        raise ValidationError("Item cannot be its own parent")
                except Item.DoesNotExist:
                    raise HttpError(404, "Parent item not found")
            
            for attr, value in data.dict(exclude_unset=True).items():
                if value is not None:  # Only update non-None values
                    setattr(item, attr, value)
                    
            item.full_clean()
            item.save()
            return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))
    
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

@router.put('/items/{item_id}/parent', response={200: ItemOut, 404: ErrorResponse, 400: ValidationErrorResponse})
def change_parent(request, item_id: int, new_parent_id: int | None = None):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            old_parent = item.parent
            
            # If new_parent_id is None, we're moving to root
            if new_parent_id is None:
                new_parent = None
            else:
                try:
                    new_parent = Item.objects.get(id=new_parent_id)
                    if new_parent == item:
                        raise ValidationError("Item cannot be its own parent")
                    
                    # Check for circular dependency
                    current = new_parent
                    while current:
                        if current == item:
                            raise ValidationError("Circular dependency detected")
                        current = current.parent
                except Item.DoesNotExist:
                    raise HttpError(404, "Parent item not found")
            
            # Only create history if parent actually changes
            if old_parent != new_parent:
                ComponentHistory.objects.create(
                    item=item,
                    old_parent=old_parent,
                    new_parent=new_parent
                )

                # Update the parent field
                item.parent = new_parent
                item.full_clean()
                item.save()
            
            return item
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))


@router.delete('/items/{item_id}', response={204: None, 404: ErrorResponse})
def delete_item(request, item_id: int):
    try:
        item = Item.objects.get(id=item_id)
        item.delete()
        return 204, None
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")

# Note endpoints
@router.post('/items/{item_id}/notes', response={201: NoteSchema, 404: ErrorResponse, 400: ValidationErrorResponse})
def create_note(request, item_id: int, data: NoteCreate):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            note = Note(item=item, **data.dict())
            note.full_clean()
            note.save()
            return 201, note
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))

@router.delete('/items/{item_id}/notes/{note_id}', response={204: None, 404: ErrorResponse})
def delete_note(request, item_id: int, note_id: int):
    try:
        note = Note.objects.get(item_id=item_id, id=note_id)
        note.delete()
        return 204, None
    except Note.DoesNotExist:
        raise HttpError(404, "Note not found")

# Email endpoints
@router.post('/items/{item_id}/emails', response={201: EmailSchema, 404: ErrorResponse, 400: ValidationErrorResponse})
def create_email(request, item_id: int, data: EmailCreate):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            email = Email(item=item, **data.dict())
            email.full_clean()
            email.save()
            return 201, email
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))

@router.delete('/items/{item_id}/emails/{email_id}', response={204: None, 404: ErrorResponse})
def delete_email(request, item_id: int, email_id: int):
    try:
        email = Email.objects.get(item_id=item_id, id=email_id)
        email.delete()
        return 204, None
    except Email.DoesNotExist:
        raise HttpError(404, "Email not found")

# Attachment endpoints
@router.post('/items/{item_id}/attachments', response={201: AttachmentSchema, 404: ErrorResponse, 400: ValidationErrorResponse})
def create_attachment(request, item_id: int, file: UploadedFile = File(...)):
    try:
        with transaction.atomic():
            item = Item.objects.get(id=item_id)
            
            # Validate file type and size
            if not file.content_type.startswith(('image/', 'application/', 'text/')):  # Added text/ for test files
                raise ValidationError({'file': ['Unsupported file type']})
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError({'file': ['File size exceeds 10MB limit']})
                
            attachment = Attachment(
                item=item,
                file=file,
                type=file.content_type
            )
            attachment.full_clean()
            attachment.save()
            return 201, attachment
    except Item.DoesNotExist:
        raise HttpError(404, "Item not found")
    except ValidationError as e:
        raise HttpError(400, dict(e))

@router.delete('/items/{item_id}/attachments/{attachment_id}', response={204: None, 404: ErrorResponse})
def delete_attachment(request, item_id: int, attachment_id: int):
    try:
        attachment = Attachment.objects.get(item_id=item_id, id=attachment_id)
        attachment.delete()
        return 204, None
    except Attachment.DoesNotExist:
        raise HttpError(404, "Attachment not found")

api.add_router('', router)
