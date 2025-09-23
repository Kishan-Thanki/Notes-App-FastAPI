import uuid
import aiofiles
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form

from .. import schemas
from ..database import users_collection 

SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

router = APIRouter(tags=["Authentication"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await users_collection.find_one({"email": email})
    if user is None:
        raise credentials_exception
    return user


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

    hashed_password = get_password_hash(password)
    new_user = {
        "email": email,
        "hashed_password": hashed_password,
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