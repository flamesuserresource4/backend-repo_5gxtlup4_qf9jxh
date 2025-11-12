import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import FileResponse
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext

from database import db, create_document, get_documents
from schemas import AdminUser, BlogPost, PartnerLogo, CaseStudy

# Environment
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 8

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

app = FastAPI(title="CMS Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------- Auth helpers ----------------------
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class AdminCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> AdminUser:
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # lookup
    user = db["adminuser"].find_one({"email": email}) if db else None
    if not user:
        raise credentials_exception
    return AdminUser(**{k: v for k, v in user.items() if k != "_id"})


# ---------------------- Auth routes ----------------------
@app.post("/auth/register", response_model=Token)
async def register_admin(payload: AdminCreate):
    if db["adminuser"].find_one({"email": payload.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = get_password_hash(payload.password)
    create_document("adminuser", AdminUser(email=payload.email, password_hash=hashed, name=payload.name or payload.email.split("@")[0]))
    token = create_access_token({"sub": payload.email})
    return Token(access_token=token)


@app.post("/auth/token", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = db["adminuser"].find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": user["email"]})
    db["adminuser"].update_one({"email": user["email"]}, {"$set": {"last_login": datetime.utcnow()}})
    return Token(access_token=token)


# ---------------------- Blog CRUD ----------------------
class BlogCreate(BaseModel):
    title: str
    slug: str
    excerpt: Optional[str] = None
    content: str
    featured_image: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    status: str = "draft"
    categories: List[str] = []
    tags: List[str] = []


@app.post("/blog", response_model=dict)
async def create_blog(item: BlogCreate, admin: AdminUser = Depends(get_current_admin)):
    create_document("blogpost", BlogPost(**item.model_dump()))
    return {"ok": True}


@app.get("/blog")
async def list_blog(status: Optional[str] = None):
    flt = {"status": status} if status else {}
    docs = get_documents("blogpost", flt)
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs


# ---------------------- Partner Logos ----------------------
class LogoCreate(BaseModel):
    name: str
    image_url: str
    alt: str
    link: Optional[str] = None
    order: int = 0
    is_active: bool = True


@app.post("/partners", response_model=dict)
async def create_logo(item: LogoCreate, admin: AdminUser = Depends(get_current_admin)):
    create_document("partnerlogo", PartnerLogo(**item.model_dump()))
    return {"ok": True}


@app.get("/partners")
async def list_logos(active: Optional[bool] = None):
    flt = {"is_active": active} if active is not None else {}
    docs = get_documents("partnerlogo", flt)
    docs = sorted(docs, key=lambda x: x.get("order", 0))
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs


# ---------------------- Case Studies ----------------------
class CaseCreate(BaseModel):
    title: str
    slug: str
    client: str
    project_date: Optional[datetime] = None
    description: Optional[str] = None
    featured_image: Optional[str] = None
    content: Optional[str] = None
    tags: List[str] = []
    gallery: List[str] = []
    status: str = "draft"


@app.post("/cases", response_model=dict)
async def create_case(item: CaseCreate, admin: AdminUser = Depends(get_current_admin)):
    create_document("casestudy", CaseStudy(**item.model_dump()))
    return {"ok": True}


@app.get("/cases")
async def list_cases(status: Optional[str] = None):
    flt = {"status": status} if status else {}
    docs = get_documents("casestudy", flt)
    for d in docs:
        d["id"] = str(d.pop("_id", ""))
    return docs


# ---------------------- Media upload (local storage placeholder) ----------------------
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/media/upload")
async def upload_media(file: UploadFile = File(...), admin: AdminUser = Depends(get_current_admin)):
    # Simple local save (placeholder for S3/R2)
    suffix = os.path.splitext(file.filename)[1]
    fname = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}{suffix}"
    dest = os.path.join(UPLOAD_DIR, fname)
    with open(dest, "wb") as f:
        f.write(await file.read())
    return {"url": f"/media/{fname}", "name": file.filename}


@app.get("/media/{name}")
async def get_media(name: str):
    path = os.path.join(UPLOAD_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path)


# ---------------------- Health & Schema ----------------------
@app.get("/")
def read_root():
    return {"message": "CMS Backend running"}


@app.get("/schema")
def schema_definitions():
    # Return model names for the built-in viewer
    return {
        "collections": [
            "adminuser",
            "blogpost",
            "partnerlogo",
            "casestudy",
        ]
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
