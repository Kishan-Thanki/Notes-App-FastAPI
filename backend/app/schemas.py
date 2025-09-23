from bson import ObjectId
from typing import Annotated
from pydantic import BaseModel, Field, EmailStr, BeforeValidator, ConfigDict

def validate_object_id(v) -> ObjectId:
    if not isinstance(v, ObjectId) and not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return ObjectId(v)

PyObjectId = Annotated[ObjectId, BeforeValidator(validate_object_id)]

class MongoModel(BaseModel):
    id: PyObjectId = Field(alias="_id")
    
    model_config = ConfigDict(
        populate_by_name=True, 
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str}
    )

class NoteBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=50)
    content: str = Field(..., max_length=300)

class NoteInDB(MongoModel, NoteBase):
    owner_email: EmailStr

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str

class UserInDB(MongoModel):
    email: EmailStr
    display_name: str

class Token(BaseModel):
    access_token: str
    token_type: str