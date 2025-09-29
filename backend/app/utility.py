import base64
import random
from bson import ObjectId
from typing import Any, Dict, List


def generate_otp(length: int = 6) -> str:
    return "".join([str(random.randint(0, 9)) for _ in range(length)])


async def send_verification_email(email: str, otp: str):
    print("================ OTP VERIFICATION ================")
    print(f"To: {email}")
    print(f"Your verification OTP is: {otp}")
    print("Note: This OTP expires in 10 minutes.")
    print("==================================================")
    return {"message": "OTP logged to server console"}


def _sanitize(value: Any) -> Any:
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_sanitize(v) for v in value]
    if isinstance(value, dict):
        return {k: _sanitize(v) for k, v in value.items() if k != "hashed_password"}
    return str(value)


def sanitize_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    return _sanitize({k: v for k, v in doc.items() if k != "hashed_password"})


