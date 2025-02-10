from ninja import Schema
from typing import List, Optional
from datetime import datetime

class CodeIdentifierSchema(Schema):
    id: int
    code: str
    source: str
    created_at: datetime
    
class ComponentHistorySchema(Schema):
    id: int
    old_parent_id: Optional[int]
    new_parent_id: Optional[int]
    action_type: str
    changed_at: datetime

class NoteSchema(Schema):
    id: int
    content: str
    created_at: datetime

class FileSchema(Schema):
    id: int
    file: str
    file_type: str
    created_at: datetime

class EmailSchema(Schema):
    id: int
    subject: str
    body: str
    from_address: str
    received_at: datetime
    created_at: datetime

class ItemBase(Schema):
    name: str
    description: Optional[str] = None
    qr_code: Optional[str] = None

class ItemCreate(ItemBase):
    parent_id: Optional[int] = None

class ItemOut(ItemBase):
    id: int
    parent_id: Optional[int]
    created_at: datetime
    level: int
    children: List['ItemOut'] = []
    history: List[ComponentHistorySchema] = []

    notes: List[NoteSchema] = []
    codes: List[CodeIdentifierSchema] = []
    files: List[FileSchema] = []
    emails: List[EmailSchema] = []
    # Add computed fields
    full_path: str
    attachment_count: int
    
    @staticmethod
    def resolve_full_path(obj):
        return obj.get_full_path()
    
    @staticmethod
    def resolve_attachment_count(obj):
        return (obj.notes.count() + obj.files.count() + 
                obj.emails.count() + obj.codes.count())
    emails: List[EmailSchema] = []