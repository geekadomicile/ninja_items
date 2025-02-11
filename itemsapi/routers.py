from ninja import Router
from ninja.errors import HttpError
from django.shortcuts import get_object_or_404
from django.db.models import Q
from mptt.exceptions import InvalidMove
from typing import List, Optional
from django.core.exceptions import ValidationError
from .models import ComponentHistory, Item
from .schemas import ComponentHistorySchema, ItemCreate, ItemOut, MovePayload
from django.db import transaction

router = Router()
@router.get("/items", response=List[ItemOut])
def list_items(request):
    """Get full inventory tree starting from root items (computers, storage, etc)"""
    return Item.objects.root_nodes().prefetch_related(*Item.get_prefetch_fields())

@router.get("/items/{item_id}", response=ItemOut)
def get_item(request, item_id: int):
    """Get item with its complete subtree (e.g., GPU with waterblock)"""
    return get_object_or_404(Item.objects.prefetch_related(*Item.get_prefetch_fields()), id=item_id)

@router.get("/items/{item_id}/path", response=List[ItemOut])
def get_component_path(request, item_id: int):
    """Get full path to component (e.g., Shop->Laptop->Motherboard->CPU)"""
    item = get_object_or_404(Item, id=item_id)
    return item.get_ancestors(include_self=True)

@router.get("/items/{item_id}/siblings", response=List[ItemOut])
def get_similar_components(request, item_id: int):
    """Get components at same level - useful for finding compatible parts"""
    item = get_object_or_404(Item, id=item_id)
    return item.get_siblings(include_self=False)

@router.get("/items/search", response=List[ItemOut])
def search_items(request, q: str):
    """Search components by name, description or QR code"""
    return Item.objects.filter(
        Q(name__icontains=q) |
        Q(description__icontains=q) |
        Q(qr_code__iexact=q)
    ).prefetch_related(*Item.get_prefetch_fields())

@router.post("/items", response={201: ItemOut})
def create_item(request, payload: ItemCreate):
    with transaction.atomic():
        parent = get_object_or_404(Item, id=payload.parent_id) if payload.parent_id else None
        item = Item.objects.create(
            name=payload.name,
            description=payload.description,
            qr_code=payload.qr_code,
            parent=parent
        )
        return 201, item
    
@router.get("/items/{item_id}/history", response=List[ComponentHistorySchema])
def get_item_history(request, item_id: int):
    """Get complete movement history for a component"""
    item = get_object_or_404(Item, id=item_id)
    return item.history.all()

@router.put("/items/{item_id}/move", response=ItemOut)
def move_item(request, item_id: int, payload: MovePayload):
    with transaction.atomic():
        item = get_object_or_404(Item, id=item_id)
        new_parent = get_object_or_404(Item, id=payload.new_parent_id) if payload.new_parent_id else None
        try:
            moved_item = item.move_under(new_parent)
            return moved_item
        except ValidationError as e:
            raise HttpError(400, str(e))


@router.delete("/items/{item_id}", response={204: None})
def delete_item(request, item_id: int):
    """Delete component and all its subcomponents"""
    item = get_object_or_404(Item, id=item_id)
    item.delete()
    return 204, None
