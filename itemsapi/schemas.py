from ninja import Schema
from typing import List, Optional
from datetime import datetime

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
    notes: List['NoteSchema'] = []
    attachments: List['AttachmentSchema'] = []
    emails: List['EmailSchema'] = []

class NoteSchema(Schema):
    id: int
    content: str
    created_at: datetime

class AttachmentSchema(Schema):
    id: int
    file: str
    type: str
    uploaded_at: datetime

class EmailSchema(Schema):
    id: int
    subject: str
    content: str
    created_at: datetime
