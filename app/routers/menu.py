from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from base import get_db
from models.menu_item import MenuItem
from models.user import User
from schemas.menu_item import MenuItemCreate, MenuItemUpdate, MenuItemResponse
from utils.auth import get_current_user, get_current_admin

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("/", response_model=list[MenuItemResponse])
async def get_menu(db: Session = Depends(get_db)):
    items = db.query(MenuItem).filter(MenuItem.is_available == True).all()
    return items


@router.get("/{item_id}", response_model=MenuItemResponse)
async def get_menu_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция не найдена"
        )
    
    return item


@router.post("/", response_model=MenuItemResponse, status_code=status.HTTP_201_CREATED)
async def create_menu_item(
    item: MenuItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    existing = db.query(MenuItem).filter(MenuItem.name == item.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Позиция с названием '{item.name}' уже существует"
        )
    
    db_item = MenuItem(**item.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.put("/{item_id}", response_model=MenuItemResponse)
async def update_menu_item(
    item_id: int,
    item: MenuItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция не найдена"
        )
    
    for key, value in item.model_dump(exclude_unset=True).items():
        setattr(db_item, key, value)
    
    db.commit()
    db.refresh(db_item)
    
    return db_item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_menu_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    db_item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    
    if not db_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция не найдена"
        )
    
    db.delete(db_item)
    db.commit()
    
    return None