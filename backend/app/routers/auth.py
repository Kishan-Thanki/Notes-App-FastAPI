import schemas
import utility
from typing import Optional
from datetime import datetime, timedelta
from database import users_collection, otps_collection
from fastapi.security import OAuth2PasswordRequestForm
from security import verify_password, create_access_token, get_current_user, get_password_hash
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form, File, UploadFile
from security import verify_password, create_access_token, get_current_user, get_password_hash

router = APIRouter(tags=["Authentication"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    display_name: Optional[str] = Form(None),
    username_form: Optional[str] = Form(None),
    username: Optional[str] = Form(None),
    email_form: Optional[str] = Form(None),
    email: Optional[str] = Form(None),
    password_form: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
):
    if request.headers.get("content-type", "").startswith("multipart/form-data"):
        username = username_form or username or display_name
        email = email_form or email
        password = password_form or password
    else:
        body = await request.json()
        user_data = schemas.UserCreate(**body)
        username = user_data.username
        email = user_data.email
        password = user_data.password

    if not username or not email or not password:
        raise HTTPException(status_code=422, detail="Missing required fields: username, email, password")

    if await users_collection.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")

    if await users_collection.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = {
        "username": username,
        "email": email,
        "hashed_password": get_password_hash(password),
        "is_verified": False,
    }

    if profile_image:
        contents = await profile_image.read()
        filename = f"{username}_{profile_image.filename}"
        with open(f"static/images/{filename}", "wb") as f:
            f.write(contents)
        new_user["profile_image"] = filename

    await users_collection.insert_one(new_user)

    otp = utility.generate_otp()
    await otps_collection.insert_one({
        "email": email,
        "otp": otp,
        "created_at": datetime.utcnow(),
    })

    await utility.send_verification_email(email, otp)

    return {"message": "User registered successfully. Please check console for the verification OTP."}

@router.post("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(verification_data: schemas.VerifyEmailRequest):
    ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)

    otp_data = await otps_collection.find_one_and_delete({
        "email": verification_data.email,
        "otp": verification_data.otp,
        "created_at": {"$gte": ten_minutes_ago}
    })

    if not otp_data:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")

    await users_collection.update_one(
        {"email": verification_data.email},
        {"$set": {"is_verified": True}}
    )

    return {"message": "Email verified successfully. You can now log in."}


@router.post("/login", response_model=schemas.Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user.get("hashed_password", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    if not user.get("is_verified", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your email before logging in.",
        )
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/profile")
async def get_profile(current_user: dict = Depends(get_current_user)):
    profile = utility.sanitize_document(current_user)
    if "profile_image" in profile:
        profile["profile_image_url"] = f"/static/images/{profile['profile_image']}"
    return profile