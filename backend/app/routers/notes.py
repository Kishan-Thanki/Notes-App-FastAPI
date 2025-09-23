from .. import schemas
from bson import ObjectId
from .auth import get_current_user 
from ..database import notes_collection
from fastapi import APIRouter, HTTPException, status, Depends

router = APIRouter(prefix="/notes", tags=["Notes"])

@router.post("/", response_model=schemas.NoteInDB, status_code=status.HTTP_201_CREATED)
async def create_note(note: schemas.NoteBase, current_user: dict = Depends(get_current_user)):
    note_dict = note.model_dump()
    note_dict["owner_email"] = current_user["email"] 
    
    new_note = await notes_collection.insert_one(note_dict)
    created_note = await notes_collection.find_one({"_id": new_note.inserted_id})
    
    return created_note

@router.get("/") 
async def get_my_notes(current_user: dict = Depends(get_current_user)):
    notes_from_db = await notes_collection.find({"owner_email": current_user["email"]}).to_list(1000)
    
    response_notes = []
    for note in notes_from_db:
        response_notes.append({
            "id": str(note["_id"]), 
            "title": note["title"],
            "content": note["content"],
            "owner_email": note["owner_email"]
        })
    
    return response_notes

@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(note_id: str, current_user: dict = Depends(get_current_user)):
    try:
        obj_id = ObjectId(note_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid note ID format")

    delete_result = await notes_collection.delete_one(
        {"_id": obj_id, "owner_email": current_user["email"]}
    )

    if delete_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    
    return