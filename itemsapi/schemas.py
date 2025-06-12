from ninja import Schema
from typing import List, Optional
from datetime import datetime
from pydantic import field_validator

# Base schemas for attachments
class AttachmentBase(Schema):
    id: int
    created_at: datetime

class CodeIdentifierSchema(AttachmentBase):
    code: str
    source: str

class ComponentHistorySchema(Schema):
    id: int
    old_parent_id: Optional[int]
    new_parent_id: Optional[int]
    action_type: str
    changed_at: datetime

class NoteCreate(Schema):
    content: str
    author: str = "System"  # Default author if not provided

class NoteSchema(AttachmentBase):
    content: str
    author: str

class FileSchema(AttachmentBase):
    file: str
    file_type: str

class EmailSchema(AttachmentBase):
    subject: str
    body: str
    from_address: str
    received_at: datetime

class EmailCreate(Schema):
    item_id: int
    subject: str
    body: str
    from_address: str
    received_at: datetime
    
# Item schemas with inheritance
class ListingUpdate(Schema):
    listing_json: str

class ItemBase(Schema):
    name: str
    description: Optional[str] = None
    qr_code: Optional[str] = None
    listing_json: Optional[str] = None
    
    # Remove level from base schema since it's computed
    @staticmethod
    def resolve_level(obj):
        return obj.get_level()
    
class MovePayload(Schema):
    new_parent_id: Optional[int] = 0
    
    @field_validator('new_parent_id')
    def validate_new_parent(cls, value):
        if value is not None and value < 0:
            raise ValueError("Parent ID must be a positive integer")
        return value

class ItemCreate(Schema):
    # Separate from ItemBase to avoid level requirement in creation
    name: str
    description: Optional[str] = None
    qr_code: Optional[str] = None
    parent_id: Optional[int] = None

class ItemOut(ItemBase):
    id: int
    parent_id: Optional[int]
    created_at: datetime
    level: int  # Include in output schema
    children: List['ItemOut'] = []
    history: List[ComponentHistorySchema] = []
    notes: List[NoteSchema] = []
    codes: List[CodeIdentifierSchema] = []
    files: List[FileSchema] = []
    emails: List[EmailSchema] = []
    full_path: str
    attachment_count: int
    listing_worker: Optional[str] = None
    
    @staticmethod
    def resolve_children(obj):
        return obj.get_children().prefetch_related(*obj.get_prefetch_fields())
    
    @staticmethod
    def resolve_full_path(obj):
        return obj.get_full_path()
    
    @staticmethod
    def resolve_attachment_count(obj):
        return (obj.notes.count() + obj.files.count() + 
                obj.emails.count() + obj.codes.count())
