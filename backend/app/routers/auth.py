import uuid
import aiofiles
from .. import schemas
from ..database import users_collection
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from ..security import verify_password, create_access_token, get_current_user, get_password_hash

router = APIRouter(tags=["Authentication"])

@router.post("/register")
async def register(
    display_name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    profile_image: UploadFile = File(...)
):
    if await users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    image_path = f"static/images/{uuid.uuid4()}.{profile_image.filename.split('.')[-1]}"
    
    async with aiofiles.open(image_path, 'wb') as out_file:
        content = await profile_image.read()
        await out_file.write(content)

    new_user = {
        "email": email,
        "hashed_password": get_password_hash(password),
        "display_name": display_name,
        "profile_image_path": image_path
    }
    
    await users_collection.insert_one(new_user)
    
    return {"message": "User registered successfully."}

@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    return {
        "display_name": current_user.get("display_name"),
        "email": current_user.get("email"),
        "profile_image_path": current_user.get("profile_image_path")
    }