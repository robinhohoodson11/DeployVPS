from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import bcrypt
from cryptography.fernet import Fernet
import paramiko
import io
import asyncio
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Config
JWT_SECRET = os.environ.get('JWT_SECRET', 'super-secret-key-change-in-production')
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION = 24 * 60  # 24 hours in minutes

# Encryption for sensitive data (SSH passwords/keys)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

app = FastAPI(title="Deploy Git to VPS")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ============ MODELS ============

class DeployStatus(str, Enum):
    PENDING = "pending"
    CLONING = "cloning"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    FAILED = "failed"
    STOPPED = "stopped"

class UserStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    EXPIRED = "expired"
    BLOCKED = "blocked"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserCreateByAdmin(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"  # user or admin
    expires_at: Optional[str] = None  # ISO date string
    send_email: bool = False

class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None
    expires_at: Optional[str] = None  # ISO date string or null to remove

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    status: str = "active"
    expires_at: Optional[str] = None
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class EmailConfig(BaseModel):
    smtp_host: str
    smtp_port: int = 587
    smtp_user: str
    smtp_password: str
    smtp_from_name: str = "DeployVPS"
    smtp_from_email: Optional[str] = None
    smtp_use_tls: bool = True

class EmailConfigResponse(BaseModel):
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_from_name: str
    smtp_from_email: Optional[str]
    smtp_use_tls: bool
    configured: bool = True

class VPSCreate(BaseModel):
    name: str
    host: str
    port: int = 22
    username: str
    auth_type: str = "password"  # password or key
    password: Optional[str] = None
    ssh_key: Optional[str] = None

class VPSResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    username: str
    auth_type: str
    status: str
    created_at: str

class DeploymentCreate(BaseModel):
    vps_id: str
    repo_url: str
    branch: str = "main"
    project_name: str
    port: int = 3000
    env_vars: Optional[dict] = None
    github_token: Optional[str] = None
    create_mongodb: bool = False
    mongodb_port: int = 27017
    create_admin: bool = False
    admin_email: str = "admin@admin.com"
    admin_password: str = "Admin@123"

class LogEntryResponse(BaseModel):
    timestamp: str
    message: str
    level: str = "info"

class DeploymentResponse(BaseModel):
    id: str
    vps_id: str
    repo_url: str
    branch: str
    project_name: str
    port: int
    status: str
    container_id: Optional[str] = None
    logs: List[LogEntryResponse] = []
    domain: Optional[str] = None
    mongodb_url: Optional[str] = None
    deploy_type: Optional[str] = None  # "frontend_only", "backend_only", "fullstack"
    backend_port: Optional[int] = None
    admin_credentials: Optional[dict] = None
    created_at: str
    updated_at: str

class DomainConfig(BaseModel):
    domain: str

class LogEntry(BaseModel):
    timestamp: str
    message: str
    level: str = "info"

# ============ AUTH HELPERS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_token(user_id: str) -> str:
    payload = {
        "sub": user_id,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION),
        "iat": datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        
        # Check if user is blocked
        if user.get("status") == "blocked":
            raise HTTPException(status_code=403, detail="Conta bloqueada. Entre em contato com o administrador.")
        
        # Check if user is pending (except admins)
        if user.get("status") == "pending" and user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Conta pendente de aprovação pelo administrador.")
        
        # Check if user has expired
        if user.get("expires_at"):
            expires = datetime.fromisoformat(user["expires_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expires:
                await db.users.update_one({"id": user_id}, {"$set": {"status": "expired"}})
                raise HTTPException(status_code=403, detail="Acesso expirado. Entre em contato com o administrador.")
        
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()

# ============ EMAIL HELPERS ============

async def send_email(to_email: str, subject: str, html_content: str):
    """Send email using configured SMTP settings"""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    
    config = await db.settings.find_one({"type": "email_config"}, {"_id": 0})
    if not config:
        logger.warning("Email not configured, skipping send")
        return False
    
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{config.get('smtp_from_name', 'DeployVPS')} <{config.get('smtp_from_email') or config['smtp_user']}>"
        msg['To'] = to_email
        
        html_part = MIMEText(html_content, 'html')
        msg.attach(html_part)
        
        smtp_password = decrypt_data(config['smtp_password_encrypted'])
        
        if config.get('smtp_use_tls', True):
            server = smtplib.SMTP(config['smtp_host'], config['smtp_port'])
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(config['smtp_host'], config['smtp_port'])
        
        server.login(config['smtp_user'], smtp_password)
        server.sendmail(msg['From'], to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

async def send_welcome_email(user_email: str, user_name: str, password: str):
    """Send welcome email with credentials"""
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #18181b; border-radius: 8px; padding: 30px;">
            <h1 style="color: #22c55e; margin-bottom: 20px;">🚀 Bem-vindo ao DeployVPS!</h1>
            <p>Olá <strong>{user_name}</strong>,</p>
            <p>Sua conta foi aprovada! Aqui estão suas credenciais de acesso:</p>
            <div style="background-color: #27272a; border-radius: 4px; padding: 15px; margin: 20px 0;">
                <p style="margin: 5px 0;"><strong>Email:</strong> {user_email}</p>
                <p style="margin: 5px 0;"><strong>Senha:</strong> {password}</p>
            </div>
            <p>Recomendamos que você altere sua senha após o primeiro acesso.</p>
            <p style="color: #71717a; margin-top: 30px; font-size: 12px;">
                Este é um email automático, não responda.
            </p>
        </div>
    </body>
    </html>
    """
    return await send_email(user_email, "🚀 Bem-vindo ao DeployVPS - Suas Credenciais", html_content)

async def send_approval_email(user_email: str, user_name: str):
    """Send approval notification email"""
    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #18181b; border-radius: 8px; padding: 30px;">
            <h1 style="color: #22c55e; margin-bottom: 20px;">✅ Conta Aprovada!</h1>
            <p>Olá <strong>{user_name}</strong>,</p>
            <p>Sua conta no DeployVPS foi aprovada pelo administrador.</p>
            <p>Você já pode acessar o sistema usando suas credenciais cadastradas.</p>
            <p style="color: #71717a; margin-top: 30px; font-size: 12px;">
                Este é um email automático, não responda.
            </p>
        </div>
    </body>
    </html>
    """
    return await send_email(user_email, "✅ Sua conta DeployVPS foi aprovada!", html_content)

# ============ AUTH ROUTES ============

@api_router.post("/auth/register")
async def register(user_data: UserCreate, background_tasks: BackgroundTasks):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # First user is admin and active, others need approval
    user_count = await db.users.count_documents({})
    is_first_user = user_count == 0
    role = "admin" if is_first_user else "user"
    status = "active" if is_first_user else "pending"
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "role": role,
        "status": status,
        "expires_at": None,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    # If user is pending, return message instead of token
    if status == "pending":
        return {
            "message": "Cadastro realizado! Aguarde a aprovação do administrador.",
            "status": "pending"
        }
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user_id, email=user_data.email, name=user_data.name, 
            role=role, status=status, expires_at=None, created_at=user["created_at"]
        )
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Email ou senha inválidos")
    
    # Check user status
    status = user.get("status", "active")
    if status == "pending":
        raise HTTPException(status_code=403, detail="Conta pendente de aprovação pelo administrador.")
    if status == "blocked":
        raise HTTPException(status_code=403, detail="Conta bloqueada. Entre em contato com o administrador.")
    
    # Check expiration
    if user.get("expires_at"):
        expires = datetime.fromisoformat(user["expires_at"].replace("Z", "+00:00"))
        if datetime.now(timezone.utc) > expires:
            await db.users.update_one({"id": user["id"]}, {"$set": {"status": "expired"}})
            raise HTTPException(status_code=403, detail="Acesso expirado. Entre em contato com o administrador.")
    
    if status == "expired":
        raise HTTPException(status_code=403, detail="Acesso expirado. Entre em contato com o administrador.")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user["id"], email=user["email"], name=user["name"], 
            role=user.get("role", "user"), status=user.get("status", "active"),
            expires_at=user.get("expires_at"), created_at=user["created_at"]
        )
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"], email=user["email"], name=user["name"], 
        role=user.get("role", "user"), status=user.get("status", "active"),
        expires_at=user.get("expires_at"), created_at=user["created_at"]
    )

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

@api_router.post("/auth/change-password")
async def change_password(data: ChangePasswordRequest, user: dict = Depends(get_current_user)):
    """Allow any authenticated user to change their password"""
    # Get user with password hash
    db_user = await db.users.find_one({"id": user["id"]}, {"_id": 0})
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Verify current password
    if not verify_password(data.current_password, db_user["password_hash"]):
        raise HTTPException(status_code=400, detail="Senha atual incorreta")
    
    # Validate new password
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="A nova senha deve ter pelo menos 6 caracteres")
    
    if data.current_password == data.new_password:
        raise HTTPException(status_code=400, detail="A nova senha deve ser diferente da atual")
    
    # Update password
    new_hash = hash_password(data.new_password)
    await db.users.update_one({"id": user["id"]}, {"$set": {"password_hash": new_hash}})
    
    return {"message": "Senha alterada com sucesso"}


# ============ ADMIN ROUTES ============

def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return user

@api_router.get("/admin/users", response_model=List[UserResponse])
async def list_users(admin: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(
        id=u["id"], email=u["email"], name=u["name"],
        role=u.get("role", "user"), status=u.get("status", "active"),
        expires_at=u.get("expires_at"), created_at=u["created_at"]
    ) for u in users]

@api_router.get("/admin/users/pending", response_model=List[UserResponse])
async def list_pending_users(admin: dict = Depends(require_admin)):
    """List users waiting for approval"""
    users = await db.users.find({"status": "pending"}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(
        id=u["id"], email=u["email"], name=u["name"],
        role=u.get("role", "user"), status=u.get("status", "pending"),
        expires_at=u.get("expires_at"), created_at=u["created_at"]
    ) for u in users]

@api_router.post("/admin/users", response_model=UserResponse)
async def create_user(user_data: UserCreateByAdmin, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "role": user_data.role,
        "status": "active",  # Admin-created users are active by default
        "expires_at": user_data.expires_at,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    # Send welcome email if requested
    if user_data.send_email:
        background_tasks.add_task(send_welcome_email, user_data.email, user_data.name, user_data.password)
    
    return UserResponse(
        id=user_id, email=user_data.email, name=user_data.name, 
        role=user_data.role, status="active", expires_at=user_data.expires_at,
        created_at=user["created_at"]
    )

@api_router.put("/admin/users/{user_id}", response_model=UserResponse)
async def update_user(user_id: str, user_data: UserUpdate, admin: dict = Depends(require_admin)):
    """Update user details including status, role, and expiration"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    update_data = {}
    if user_data.name is not None:
        update_data["name"] = user_data.name
    if user_data.role is not None:
        if user_data.role not in ["admin", "user"]:
            raise HTTPException(status_code=400, detail="Role deve ser 'admin' ou 'user'")
        update_data["role"] = user_data.role
    if user_data.status is not None:
        if user_data.status not in ["pending", "active", "expired", "blocked"]:
            raise HTTPException(status_code=400, detail="Status inválido")
        update_data["status"] = user_data.status
    if user_data.expires_at is not None:
        update_data["expires_at"] = user_data.expires_at if user_data.expires_at != "" else None
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    return UserResponse(
        id=updated_user["id"], email=updated_user["email"], name=updated_user["name"],
        role=updated_user.get("role", "user"), status=updated_user.get("status", "active"),
        expires_at=updated_user.get("expires_at"), created_at=updated_user["created_at"]
    )

@api_router.post("/admin/users/{user_id}/approve")
async def approve_user(user_id: str, background_tasks: BackgroundTasks, admin: dict = Depends(require_admin)):
    """Approve a pending user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Usuário não está pendente")
    
    await db.users.update_one({"id": user_id}, {"$set": {"status": "active"}})
    
    # Send approval email
    background_tasks.add_task(send_approval_email, user["email"], user["name"])
    
    return {"message": "Usuário aprovado com sucesso"}

@api_router.post("/admin/users/{user_id}/reject")
async def reject_user(user_id: str, admin: dict = Depends(require_admin)):
    """Reject and delete a pending user"""
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    if user.get("status") != "pending":
        raise HTTPException(status_code=400, detail="Usuário não está pendente")
    
    await db.users.delete_one({"id": user_id})
    return {"message": "Usuário rejeitado e removido"}

@api_router.post("/admin/users/{user_id}/block")
async def block_user(user_id: str, admin: dict = Depends(require_admin)):
    """Block a user"""
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Não pode bloquear a si mesmo")
    
    result = await db.users.update_one({"id": user_id}, {"$set": {"status": "blocked"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário bloqueado"}

@api_router.post("/admin/users/{user_id}/unblock")
async def unblock_user(user_id: str, admin: dict = Depends(require_admin)):
    """Unblock a user"""
    result = await db.users.update_one({"id": user_id}, {"$set": {"status": "active"}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": "Usuário desbloqueado"}

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(require_admin)):
    if user_id == admin["id"]:
        raise HTTPException(status_code=400, detail="Não pode deletar a si mesmo")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # Also delete user's VPS and deployments
    await db.vps.delete_many({"user_id": user_id})
    await db.deployments.delete_many({"user_id": user_id})
    
    return {"message": "Usuário deletado"}

@api_router.put("/admin/users/{user_id}/role")
async def update_user_role(user_id: str, role: str, admin: dict = Depends(require_admin)):
    if role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role deve ser 'admin' ou 'user'")
    
    result = await db.users.update_one({"id": user_id}, {"$set": {"role": role}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {"message": f"Role atualizado para {role}"}

# ============ EMAIL CONFIG ROUTES ============

@api_router.get("/admin/settings/email")
async def get_email_config(admin: dict = Depends(require_admin)):
    """Get email configuration (without password)"""
    config = await db.settings.find_one({"type": "email_config"}, {"_id": 0})
    if not config:
        return {"configured": False}
    
    return EmailConfigResponse(
        smtp_host=config.get("smtp_host", ""),
        smtp_port=config.get("smtp_port", 587),
        smtp_user=config.get("smtp_user", ""),
        smtp_from_name=config.get("smtp_from_name", "DeployVPS"),
        smtp_from_email=config.get("smtp_from_email"),
        smtp_use_tls=config.get("smtp_use_tls", True),
        configured=True
    )

@api_router.post("/admin/settings/email")
async def save_email_config(config: EmailConfig, admin: dict = Depends(require_admin)):
    """Save email configuration"""
    config_data = {
        "type": "email_config",
        "smtp_host": config.smtp_host,
        "smtp_port": config.smtp_port,
        "smtp_user": config.smtp_user,
        "smtp_password_encrypted": encrypt_data(config.smtp_password),
        "smtp_from_name": config.smtp_from_name,
        "smtp_from_email": config.smtp_from_email or config.smtp_user,
        "smtp_use_tls": config.smtp_use_tls,
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.settings.update_one(
        {"type": "email_config"},
        {"$set": config_data},
        upsert=True
    )
    
    return {"message": "Configuração de email salva com sucesso"}

@api_router.post("/admin/settings/email/test")
async def test_email_config(admin: dict = Depends(require_admin)):
    """Send a test email to admin"""
    result = await send_email(
        admin["email"],
        "🧪 Teste de Email - DeployVPS",
        f"""
        <html>
        <body style="font-family: Arial, sans-serif; background-color: #09090b; color: #fafafa; padding: 20px;">
            <div style="max-width: 600px; margin: 0 auto; background-color: #18181b; border-radius: 8px; padding: 30px;">
                <h1 style="color: #22c55e;">✅ Email Configurado!</h1>
                <p>Este é um email de teste do DeployVPS.</p>
                <p>Se você está recebendo esta mensagem, a configuração de email está funcionando corretamente.</p>
            </div>
        </body>
        </html>
        """
    )
    
    if result:
        return {"message": f"Email de teste enviado para {admin['email']}"}
    else:
        raise HTTPException(status_code=500, detail="Falha ao enviar email. Verifique as configurações.")

# ============ ADMIN STATS ============

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(require_admin)):
    """Get admin dashboard statistics"""
    total_users = await db.users.count_documents({})
    pending_users = await db.users.count_documents({"status": "pending"})
    active_users = await db.users.count_documents({"status": "active"})
    expired_users = await db.users.count_documents({"status": "expired"})
    blocked_users = await db.users.count_documents({"status": "blocked"})
    admin_users = await db.users.count_documents({"role": "admin"})
    
    return {
        "total_users": total_users,
        "pending_users": pending_users,
        "active_users": active_users,
        "expired_users": expired_users,
        "blocked_users": blocked_users,
        "admin_users": admin_users
    }

# ============ VPS ROUTES ============

@api_router.post("/vps", response_model=VPSResponse)
async def create_vps(vps_data: VPSCreate, user: dict = Depends(get_current_user)):
    vps_id = str(uuid.uuid4())
    vps = {
        "id": vps_id,
        "user_id": user["id"],
        "name": vps_data.name,
        "host": vps_data.host,
        "port": vps_data.port,
        "username": vps_data.username,
        "auth_type": vps_data.auth_type,
        "password_encrypted": encrypt_data(vps_data.password) if vps_data.password else None,
        "ssh_key_encrypted": encrypt_data(vps_data.ssh_key) if vps_data.ssh_key else None,
        "status": "active",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.vps.insert_one(vps)
    return VPSResponse(
        id=vps_id, name=vps_data.name, host=vps_data.host, port=vps_data.port,
        username=vps_data.username, auth_type=vps_data.auth_type, status="active", created_at=vps["created_at"]
    )

@api_router.get("/vps", response_model=List[VPSResponse])
async def list_vps(user: dict = Depends(get_current_user)):
    vps_list = await db.vps.find({"user_id": user["id"]}, {"_id": 0, "password_encrypted": 0, "ssh_key_encrypted": 0}).to_list(100)
    return [VPSResponse(**v) for v in vps_list]

@api_router.get("/vps/{vps_id}", response_model=VPSResponse)
async def get_vps(vps_id: str, user: dict = Depends(get_current_user)):
    vps = await db.vps.find_one({"id": vps_id, "user_id": user["id"]}, {"_id": 0, "password_encrypted": 0, "ssh_key_encrypted": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    return VPSResponse(**vps)

@api_router.delete("/vps/{vps_id}")
async def delete_vps(vps_id: str, user: dict = Depends(get_current_user)):
    result = await db.vps.delete_one({"id": vps_id, "user_id": user["id"]})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="VPS not found")
    return {"message": "VPS deleted"}

@api_router.post("/vps/{vps_id}/test")
async def test_vps_connection(vps_id: str, user: dict = Depends(get_current_user)):
    vps = await db.vps.find_one({"id": vps_id, "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        if vps["auth_type"] == "password" and vps.get("password_encrypted"):
            ssh.connect(vps["host"], port=vps["port"], username=vps["username"], 
                       password=decrypt_data(vps["password_encrypted"]), timeout=10)
        elif vps["auth_type"] == "key" and vps.get("ssh_key_encrypted"):
            key_data = decrypt_data(vps["ssh_key_encrypted"])
            key = paramiko.RSAKey.from_private_key(io.StringIO(key_data))
            ssh.connect(vps["host"], port=vps["port"], username=vps["username"], pkey=key, timeout=10)
        else:
            raise HTTPException(status_code=400, detail="Invalid auth configuration")
        
        stdin, stdout, stderr = ssh.exec_command("echo 'Connection successful' && docker --version")
        output = stdout.read().decode()
        ssh.close()
        
        return {"status": "success", "message": output.strip()}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ============ DEPLOYMENT HELPERS ============

async def add_deployment_log(deployment_id: str, message: str, level: str = "info"):
    log = {"timestamp": datetime.now(timezone.utc).isoformat(), "message": message, "level": level}
    await db.deployments.update_one({"id": deployment_id}, {"$push": {"logs": log}})

async def update_deployment_status(deployment_id: str, status: str, **extra):
    update = {"status": status, "updated_at": datetime.now(timezone.utc).isoformat(), **extra}
    await db.deployments.update_one({"id": deployment_id}, {"$set": update})

def get_ssh_client(vps: dict):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if vps["auth_type"] == "password" and vps.get("password_encrypted"):
        ssh.connect(vps["host"], port=vps["port"], username=vps["username"],
                   password=decrypt_data(vps["password_encrypted"]), timeout=30)
    elif vps["auth_type"] == "key" and vps.get("ssh_key_encrypted"):
        key_data = decrypt_data(vps["ssh_key_encrypted"])
        key = paramiko.RSAKey.from_private_key(io.StringIO(key_data))
        ssh.connect(vps["host"], port=vps["port"], username=vps["username"], pkey=key, timeout=30)
    
    return ssh

async def create_admin_user(ssh, mongodb_port: int, admin_email: str, admin_password: str, deployment_id: str, db_name: str = "app"):
    """Create admin user in the deployed application's MongoDB"""
    try:
        await add_deployment_log(deployment_id, f"Creating admin user: {admin_email}...")
        
        # Generate bcrypt hash for password - MUST generate from actual password!
        password_hash = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt()).decode()
        user_id = str(uuid.uuid4())
        
        # Escape special characters for MongoDB shell
        escaped_hash = password_hash.replace("$", "\\$")
        
        # Create the admin user document with properly generated hash
        admin_script = f'''
docker exec mongodb_{db_name} mongosh --eval '
db = db.getSiblingDB("{db_name}");
// Delete existing admin if exists
db.users.deleteMany({{email: "{admin_email}"}});
db.users.insertOne({{
    "id": "{user_id}",
    "name": "Administrador",
    "email": "{admin_email}",
    "password": "{password_hash}",
    "role": "admin",
    "status": "active",
    "created_at": new Date().toISOString()
}});
print("Admin user created successfully!");
'
'''
        stdin, stdout, stderr = ssh.exec_command(admin_script)
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        if "Admin user created successfully" in output or stdout.channel.recv_exit_status() == 0:
            await add_deployment_log(deployment_id, f"✅ Admin user created!", "success")
            await add_deployment_log(deployment_id, f"📧 Email: {admin_email}", "success")
            await add_deployment_log(deployment_id, f"🔑 Password: {admin_password}", "success")
            await db.deployments.update_one(
                {"id": deployment_id}, 
                {"$set": {"admin_credentials": {"email": admin_email, "password": admin_password}}}
            )
            return True
        else:
            await add_deployment_log(deployment_id, f"Warning: Could not create admin user - {error}", "warning")
            return False
    except Exception as e:
        await add_deployment_log(deployment_id, f"Warning: Admin creation failed - {str(e)}", "warning")
        return False

async def run_deployment(deployment_id: str, vps: dict, deployment: dict, is_redeploy: bool = False):
    """
    Run deployment process. 
    If is_redeploy=True, preserves MongoDB data and only rebuilds frontend/backend.
    """
    try:
        await update_deployment_status(deployment_id, DeployStatus.CLONING)
        if is_redeploy:
            await add_deployment_log(deployment_id, "🔄 Starting REDEPLOY (preserving database)...")
        else:
            await add_deployment_log(deployment_id, "Starting deployment...")
        
        ssh = get_ssh_client(vps)
        project_name = deployment["project_name"]
        repo_url = deployment["repo_url"]
        branch = deployment["branch"]
        port = deployment["port"]
        backend_port = port + 1000  # Backend will run on port + 1000
        
        # Add GitHub token if provided for private repos
        if deployment.get("github_token_encrypted"):
            token = decrypt_data(deployment["github_token_encrypted"])
            if "github.com" in repo_url:
                repo_url = repo_url.replace("https://", f"https://{token}@")
        
        base_dir = f"/opt/deployments/{project_name}"
        
        await add_deployment_log(deployment_id, f"Creating directory: {base_dir}")
        stdin, stdout, stderr = ssh.exec_command(f"mkdir -p {base_dir}")
        stdout.channel.recv_exit_status()
        
        await add_deployment_log(deployment_id, f"Cloning repository: {deployment['repo_url']}")
        stdin, stdout, stderr = ssh.exec_command(f"cd {base_dir} && rm -rf app && git clone -b {branch} {repo_url} app 2>&1")
        clone_output = stdout.read().decode()
        clone_error = stderr.read().decode()
        await add_deployment_log(deployment_id, clone_output or clone_error)
        
        if stdout.channel.recv_exit_status() != 0:
            raise Exception(f"Git clone failed: {clone_error}")
        
        await update_deployment_status(deployment_id, DeployStatus.BUILDING)
        await add_deployment_log(deployment_id, "Analyzing project structure...")
        
        # Check project structure
        stdin, stdout, stderr = ssh.exec_command(f"test -f {base_dir}/app/Dockerfile && echo 'exists'")
        has_dockerfile = "exists" in stdout.read().decode()
        
        stdin, stdout, stderr = ssh.exec_command(f"test -f {base_dir}/app/package.json && echo 'node'")
        is_node = "node" in stdout.read().decode()
        
        stdin, stdout, stderr = ssh.exec_command(f"test -f {base_dir}/app/frontend/package.json && echo 'frontend'")
        has_frontend = "frontend" in stdout.read().decode()
        
        stdin, stdout, stderr = ssh.exec_command(f"test -f {base_dir}/app/requirements.txt && echo 'python'")
        is_python = "python" in stdout.read().decode()
        
        stdin, stdout, stderr = ssh.exec_command(f"test -f {base_dir}/app/backend/requirements.txt && echo 'backend'")
        has_backend = "backend" in stdout.read().decode()
        
        # Determine deploy type
        is_fullstack = has_frontend and has_backend
        deploy_type = "fullstack" if is_fullstack else ("frontend_only" if has_frontend else ("backend_only" if has_backend or is_python else "static"))
        
        await add_deployment_log(deployment_id, f"Detected project type: {deploy_type.upper()}")
        await db.deployments.update_one({"id": deployment_id}, {"$set": {"deploy_type": deploy_type}})
        
        # Get VPS host for CORS configuration
        vps_host = vps["host"]
        
        # Prepare env vars
        env_string = ""
        if deployment.get("env_vars"):
            for key, value in deployment["env_vars"].items():
                env_string += f" -e {key}='{value}'"
        
        # Add CORS_ORIGINS for fullstack deployments
        if is_fullstack:
            cors_origins = f"http://{vps_host}:{port},http://{vps_host}:{backend_port},http://localhost:{port},http://localhost:{backend_port},*"
            env_string += f" -e CORS_ORIGINS='{cors_origins}'"
            env_string += f" -e ALLOWED_ORIGINS='{cors_origins}'"
        
        # Create MongoDB container if requested
        mongodb_url = None
        mongodb_port_used = deployment.get("mongodb_port", 27017)
        mongodb_container = f"mongodb_{project_name}"
        network_name = f"network_{project_name}"
        mongodb_volume = f"mongodb_data_{project_name}"
        
        # Create Docker network BEFORE creating containers
        ssh.exec_command(f"docker network create {network_name} 2>/dev/null || true")
        
        if deployment.get("create_mongodb"):
            # Internal MongoDB URL for container communication
            mongodb_url_internal = f"mongodb://{mongodb_container}:27017/{project_name}"
            mongodb_url_external = f"mongodb://localhost:{mongodb_port_used}/{project_name}"
            
            if is_redeploy:
                # ========== REDEPLOY: Preserve existing MongoDB ==========
                await add_deployment_log(deployment_id, f"🗄️ Checking existing MongoDB container...")
                
                # Check if MongoDB container is running
                stdin, stdout, stderr = ssh.exec_command(f"docker ps --filter name={mongodb_container} --format '{{{{.Names}}}}'")
                running_containers = stdout.read().decode().strip()
                
                if mongodb_container in running_containers:
                    await add_deployment_log(deployment_id, f"✅ MongoDB container found and running - preserving data", "success")
                    # Ensure container is connected to the network
                    ssh.exec_command(f"docker network connect {network_name} {mongodb_container} 2>/dev/null || true")
                else:
                    # Check if container exists but is stopped
                    stdin, stdout, stderr = ssh.exec_command(f"docker ps -a --filter name={mongodb_container} --format '{{{{.Names}}}}'")
                    all_containers = stdout.read().decode().strip()
                    
                    if mongodb_container in all_containers:
                        await add_deployment_log(deployment_id, f"🔄 Restarting stopped MongoDB container (data preserved)...")
                        ssh.exec_command(f"docker start {mongodb_container}")
                        ssh.exec_command(f"docker network connect {network_name} {mongodb_container} 2>/dev/null || true")
                        await asyncio.sleep(3)
                        await add_deployment_log(deployment_id, f"✅ MongoDB container restarted - data intact", "success")
                    else:
                        # Container doesn't exist, check if volume exists
                        stdin, stdout, stderr = ssh.exec_command(f"docker volume ls --filter name={mongodb_volume} --format '{{{{.Name}}}}'")
                        existing_volume = stdout.read().decode().strip()
                        
                        if mongodb_volume in existing_volume:
                            await add_deployment_log(deployment_id, f"🔄 Recreating MongoDB container with existing data volume...")
                            mongo_cmd = f"docker run -d --name {mongodb_container} --network {network_name} -p {mongodb_port_used}:27017 -v {mongodb_volume}:/data/db --restart unless-stopped mongo:6"
                            stdin, stdout, stderr = ssh.exec_command(mongo_cmd)
                            if stdout.channel.recv_exit_status() == 0:
                                await add_deployment_log(deployment_id, f"✅ MongoDB container recreated - data restored from volume", "success")
                            else:
                                await add_deployment_log(deployment_id, f"⚠️ Failed to recreate MongoDB: {stderr.read().decode()}", "warning")
                        else:
                            await add_deployment_log(deployment_id, f"⚠️ No existing MongoDB data found - creating new instance", "warning")
                            ssh.exec_command(f"docker volume create {mongodb_volume}")
                            mongo_cmd = f"docker run -d --name {mongodb_container} --network {network_name} -p {mongodb_port_used}:27017 -v {mongodb_volume}:/data/db --restart unless-stopped mongo:6"
                            ssh.exec_command(mongo_cmd)
                
                await asyncio.sleep(2)
            else:
                # ========== NEW DEPLOY: Create fresh MongoDB ==========
                await add_deployment_log(deployment_id, f"Setting up MongoDB container on port {mongodb_port_used}...")
                
                ssh.exec_command(f"docker stop {mongodb_container} 2>/dev/null; docker rm {mongodb_container} 2>/dev/null")
                await asyncio.sleep(1)
                
                ssh.exec_command(f"docker volume create {mongodb_volume}")
                
                # Run MongoDB in the shared network so containers can communicate via hostname
                mongo_cmd = f"docker run -d --name {mongodb_container} --network {network_name} -p {mongodb_port_used}:27017 -v {mongodb_volume}:/data/db --restart unless-stopped mongo:6"
                stdin, stdout, stderr = ssh.exec_command(mongo_cmd)
                mongo_output = stdout.read().decode()
                
                if stdout.channel.recv_exit_status() == 0:
                    await add_deployment_log(deployment_id, f"MongoDB running on port {mongodb_port_used}", "success")
                    await add_deployment_log(deployment_id, f"Internal URL: {mongodb_url_internal}", "info")
                    await asyncio.sleep(3)  # Wait for MongoDB to be ready
                else:
                    await add_deployment_log(deployment_id, f"Warning: Failed to start MongoDB - {stderr.read().decode()}", "warning")
            
            # Set environment variables for MongoDB connection (both new deploy and redeploy)
            env_string += f" -e MONGO_URL='{mongodb_url_internal}'"
            env_string += f" -e MONGODB_URL='{mongodb_url_internal}'"
            env_string += f" -e DATABASE_URL='{mongodb_url_internal}'"
            env_string += f" -e DB_NAME='{project_name}'"
            await db.deployments.update_one({"id": deployment_id}, {"$set": {"mongodb_url": mongodb_url_external}})
        
        # ============ FULLSTACK DEPLOYMENT ============
        if is_fullstack:
            await add_deployment_log(deployment_id, f"🚀 Starting FULLSTACK deployment...")
            await add_deployment_log(deployment_id, f"Frontend port: {port} | Backend port: {backend_port}")
            await db.deployments.update_one({"id": deployment_id}, {"$set": {"backend_port": backend_port}})
            
            # Network already created above, just ensure it exists
            ssh.exec_command(f"docker network create {network_name} 2>/dev/null || true")
            
            # ---- BUILD AND RUN BACKEND ----
            await add_deployment_log(deployment_id, "Building backend...")
            backend_container = f"backend_{project_name}"
            
            # Base64 encoded Python script to fix CORS
            import base64
            cors_fix_script = '''
import re
with open("server.py", "r") as f:
    content = f.read()
if "CORSMiddleware" in content:
    content = re.sub(r"app\\.add_middleware\\(\\s*CORSMiddleware[^)]+\\)\\s*,?\\s*\\)", "", content, flags=re.DOTALL)
    cors_code = "\\n# CORS Auto-patched\\nfrom starlette.middleware.cors import CORSMiddleware\\napp.add_middleware(CORSMiddleware, allow_origins=[\\"*\\"], allow_credentials=False, allow_methods=[\\"*\\"], allow_headers=[\\"*\\"])\\n"
    content = re.sub(r"(app\\s*=\\s*FastAPI\\([^)]*\\))", r"\\1" + cors_code, content)
    with open("server.py", "w") as f:
        f.write(content)
    print("CORS fixed!")
'''
            cors_script_b64 = base64.b64encode(cors_fix_script.encode()).decode()
            
            backend_dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
RUN echo "{cors_script_b64}" | base64 -d | python3
ENV PORT={backend_port}
EXPOSE {backend_port}
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "{backend_port}"]
"""
            sftp = ssh.open_sftp()
            with sftp.file(f"{base_dir}/app/Dockerfile.backend", "w") as f:
                f.write(backend_dockerfile)
            sftp.close()
            
            stdin, stdout, stderr = ssh.exec_command(f"cd {base_dir}/app && docker build --no-cache -f Dockerfile.backend -t {backend_container}:latest . 2>&1")
            build_output = stdout.read().decode()
            await add_deployment_log(deployment_id, build_output[-1500:] if len(build_output) > 1500 else build_output)
            
            if stdout.channel.recv_exit_status() != 0:
                raise Exception("Backend build failed")
            
            # Stop and remove existing backend container (wait for completion)
            await add_deployment_log(deployment_id, "Stopping existing backend container...", "info")
            stdin, stdout, stderr = ssh.exec_command(f"docker stop {backend_container} 2>/dev/null; docker rm -f {backend_container} 2>/dev/null; echo 'done'")
            stdout.channel.recv_exit_status()  # Wait for command to complete
            await asyncio.sleep(2)
            
            # Run backend container
            backend_env = env_string + f" -e PORT={backend_port}"
            run_backend = f"docker run -d --name {backend_container} --network {network_name} -p {backend_port}:{backend_port} --restart unless-stopped {backend_env} {backend_container}:latest"
            stdin, stdout, stderr = ssh.exec_command(run_backend)
            backend_container_id = stdout.read().decode().strip()[:12]
            
            if stdout.channel.recv_exit_status() != 0:
                raise Exception(f"Failed to start backend: {stderr.read().decode()}")
            
            await add_deployment_log(deployment_id, f"Backend running on port {backend_port}", "success")
            
            # ---- BUILD AND RUN FRONTEND ----
            await add_deployment_log(deployment_id, "Building frontend...")
            frontend_container = f"frontend_{project_name}"
            
            # Get VPS host for frontend to connect to backend
            vps_host = vps["host"]
            
            frontend_dockerfile = f"""FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN rm -f package-lock.json
RUN npm install --legacy-peer-deps
RUN npm install ajv@^8.12.0 ajv-keywords@^5.1.0 --legacy-peer-deps 2>/dev/null || true
COPY frontend/ .
ENV CI=false
ENV DISABLE_ESLINT_PLUGIN=true
ENV REACT_APP_BACKEND_URL=http://{vps_host}:{backend_port}
ENV REACT_APP_API_URL=http://{vps_host}:{backend_port}/api
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
RUN echo 'server {{ \\
    listen 80; \\
    location / {{ \\
        root /usr/share/nginx/html; \\
        index index.html index.htm; \\
        try_files $uri $uri/ /index.html; \\
    }} \\
}}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
            sftp = ssh.open_sftp()
            with sftp.file(f"{base_dir}/app/Dockerfile.frontend", "w") as f:
                f.write(frontend_dockerfile)
            sftp.close()
            
            stdin, stdout, stderr = ssh.exec_command(f"cd {base_dir}/app && docker build --no-cache -f Dockerfile.frontend -t {frontend_container}:latest . 2>&1")
            build_output = stdout.read().decode()
            await add_deployment_log(deployment_id, build_output[-1500:] if len(build_output) > 1500 else build_output)
            
            if stdout.channel.recv_exit_status() != 0:
                raise Exception("Frontend build failed")
            
            # Stop and remove existing frontend container (wait for completion)
            await add_deployment_log(deployment_id, "Stopping existing frontend container...", "info")
            stdin, stdout, stderr = ssh.exec_command(f"docker stop {frontend_container} 2>/dev/null; docker rm -f {frontend_container} 2>/dev/null; echo 'done'")
            stdout.channel.recv_exit_status()  # Wait for command to complete
            await asyncio.sleep(2)
            
            # Run frontend container
            run_frontend = f"docker run -d --name {frontend_container} --network {network_name} -p {port}:80 --restart unless-stopped {frontend_container}:latest"
            stdin, stdout, stderr = ssh.exec_command(run_frontend)
            container_id = stdout.read().decode().strip()[:12]
            
            if stdout.channel.recv_exit_status() != 0:
                raise Exception(f"Failed to start frontend: {stderr.read().decode()}")
            
            await add_deployment_log(deployment_id, f"Frontend running on port {port}", "success")
            
            # Open firewall ports
            ssh.exec_command(f"sudo ufw allow {port}/tcp 2>/dev/null || true")
            ssh.exec_command(f"sudo ufw allow {backend_port}/tcp 2>/dev/null || true")
            
            # Create admin user if requested and MongoDB is available (only on new deploy, not redeploy)
            if not is_redeploy and deployment.get("create_admin") and deployment.get("create_mongodb"):
                await asyncio.sleep(2)  # Wait for services to be ready
                admin_email = deployment.get("admin_email", "admin@admin.com")
                admin_password = deployment.get("admin_password", "Admin@123")
                await create_admin_user(ssh, mongodb_port_used, admin_email, admin_password, deployment_id, project_name)
            
            await update_deployment_status(deployment_id, DeployStatus.RUNNING, container_id=container_id)
            if is_redeploy:
                await add_deployment_log(deployment_id, f"🎉 FULLSTACK REDEPLOY successful! (Database preserved)", "success")
            else:
                await add_deployment_log(deployment_id, f"🎉 FULLSTACK deployment successful!", "success")
            await add_deployment_log(deployment_id, f"🌐 Frontend: http://{vps_host}:{port}", "success")
            await add_deployment_log(deployment_id, f"⚙️ Backend API: http://{vps_host}:{backend_port}/api", "success")
            
        # ============ SINGLE CONTAINER DEPLOYMENT ============
        else:
            if not has_dockerfile:
                if has_frontend:
                    await add_deployment_log(deployment_id, "Detected frontend-only project")
                    dockerfile = f"""FROM node:18-alpine as build
WORKDIR /app
COPY frontend/package*.json ./
RUN rm -f package-lock.json
RUN npm install --legacy-peer-deps
RUN npm install ajv@^8.12.0 ajv-keywords@^5.1.0 --legacy-peer-deps 2>/dev/null || true
COPY frontend/ .
ENV CI=false
ENV DISABLE_ESLINT_PLUGIN=true
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
RUN echo 'server {{ \\
    listen 80; \\
    location / {{ \\
        root /usr/share/nginx/html; \\
        index index.html index.htm; \\
        try_files $uri $uri/ /index.html; \\
    }} \\
}}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
                elif is_node:
                    dockerfile = f"""FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build 2>/dev/null || true
EXPOSE {port}
CMD ["npm", "start"]
"""
                elif is_python or has_backend:
                    dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY {"backend/" if has_backend else ""}requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY {"backend/" if has_backend else ""}. .
EXPOSE {port}
CMD ["python", "-m", "uvicorn", "server:app", "--host", "0.0.0.0", "--port", "{port}"]
"""
                else:
                    dockerfile = f"""FROM nginx:alpine
WORKDIR /app
COPY . /app
RUN if [ -d "/app/public" ]; then cp -r /app/public/* /usr/share/nginx/html/; \\
    elif [ -d "/app/dist" ]; then cp -r /app/dist/* /usr/share/nginx/html/; \\
    elif [ -d "/app/build" ]; then cp -r /app/build/* /usr/share/nginx/html/; \\
    elif [ -f "/app/index.html" ]; then cp -r /app/* /usr/share/nginx/html/; \\
    else find /app -name 'index.html' -exec dirname {{}} \\; | head -1 | xargs -I {{}} cp -r {{}}/* /usr/share/nginx/html/; fi
RUN rm -f /usr/share/nginx/html/Dockerfile /usr/share/nginx/html/*.md /usr/share/nginx/html/.git* 2>/dev/null || true
RUN echo 'server {{ \\
    listen 80; \\
    location / {{ \\
        root /usr/share/nginx/html; \\
        index index.html index.htm; \\
        try_files $uri $uri/ /index.html; \\
    }} \\
}}' > /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""
                
                await add_deployment_log(deployment_id, f"Creating Dockerfile for {deploy_type} project")
                sftp = ssh.open_sftp()
                with sftp.file(f"{base_dir}/app/Dockerfile", "w") as f:
                    f.write(dockerfile)
                sftp.close()
            
            # Build Docker image
            await add_deployment_log(deployment_id, "Building Docker image...")
            container_name = f"deploy_{project_name}"
            
            stdin, stdout, stderr = ssh.exec_command(f"cd {base_dir}/app && docker build --no-cache -t {container_name}:latest . 2>&1")
            build_output = stdout.read().decode()
            await add_deployment_log(deployment_id, build_output[-2000:] if len(build_output) > 2000 else build_output)
            
            if stdout.channel.recv_exit_status() != 0:
                raise Exception("Docker build failed")
            
            await update_deployment_status(deployment_id, DeployStatus.DEPLOYING)
            await add_deployment_log(deployment_id, "Stopping existing container if any...")
            
            ssh.exec_command(f"docker stop {container_name} 2>/dev/null; docker rm {container_name} 2>/dev/null")
            await asyncio.sleep(2)
            
            # Open firewall port
            await add_deployment_log(deployment_id, f"Opening firewall port {port}...")
            ssh.exec_command(f"sudo ufw allow {port}/tcp 2>/dev/null || sudo iptables -A INPUT -p tcp --dport {port} -j ACCEPT 2>/dev/null || true")
            await asyncio.sleep(1)
            
            # Determine internal port
            is_static = not has_dockerfile and not is_node and not is_python and not has_frontend and not has_backend
            internal_port = 80 if (is_static or has_frontend) else port
            
            # Stop existing container if exists (for redeploy)
            ssh.exec_command(f"docker stop {container_name} 2>/dev/null; docker rm {container_name} 2>/dev/null")
            await asyncio.sleep(1)
            
            # Run container
            await add_deployment_log(deployment_id, f"Starting container on port {port}...")
            run_cmd = f"docker run -d --name {container_name} -p {port}:{internal_port} --restart unless-stopped {env_string} {container_name}:latest"
            stdin, stdout, stderr = ssh.exec_command(run_cmd)
            container_id = stdout.read().decode().strip()[:12]
            
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                raise Exception(f"Failed to start container: {error}")
            
            # Create admin user if requested and MongoDB is available (only on new deploy, not redeploy)
            if not is_redeploy and deployment.get("create_admin") and deployment.get("create_mongodb"):
                await asyncio.sleep(2)
                admin_email = deployment.get("admin_email", "admin@admin.com")
                admin_password = deployment.get("admin_password", "Admin@123")
                await create_admin_user(ssh, mongodb_port_used, admin_email, admin_password, deployment_id, project_name)
            
            await update_deployment_status(deployment_id, DeployStatus.RUNNING, container_id=container_id)
            if is_redeploy:
                await add_deployment_log(deployment_id, f"Redeploy successful! Container ID: {container_id} (Database preserved)", "success")
            else:
                await add_deployment_log(deployment_id, f"Deployment successful! Container ID: {container_id}", "success")
            await add_deployment_log(deployment_id, f"Application running on http://{vps['host']}:{port}", "success")
        
        ssh.close()
        
    except Exception as e:
        logger.error(f"Deployment failed: {e}")
        await update_deployment_status(deployment_id, DeployStatus.FAILED)
        await add_deployment_log(deployment_id, f"Deployment failed: {str(e)}", "error")

# ============ DEPLOYMENT ROUTES ============

@api_router.post("/deployments", response_model=DeploymentResponse)
async def create_deployment(data: DeploymentCreate, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    vps = await db.vps.find_one({"id": data.vps_id, "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    # Check if port is already in use on this VPS
    existing_deployment = await db.deployments.find_one({
        "vps_id": data.vps_id, 
        "port": data.port,
        "status": {"$in": ["running", "pending", "cloning", "building", "deploying"]}
    })
    if existing_deployment:
        raise HTTPException(
            status_code=400, 
            detail=f"Porta {data.port} já está em uso pelo projeto '{existing_deployment['project_name']}' nesta VPS. Use outra porta."
        )
    
    deployment_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    
    deployment = {
        "id": deployment_id,
        "user_id": user["id"],
        "vps_id": data.vps_id,
        "repo_url": data.repo_url,
        "branch": data.branch,
        "project_name": data.project_name,
        "port": data.port,
        "env_vars": data.env_vars,
        "github_token_encrypted": encrypt_data(data.github_token) if data.github_token else None,
        "create_mongodb": data.create_mongodb,
        "mongodb_port": data.mongodb_port,
        "create_admin": data.create_admin,
        "admin_email": data.admin_email,
        "admin_password": data.admin_password,
        "status": DeployStatus.PENDING,
        "container_id": None,
        "logs": [],
        "domain": None,
        "mongodb_url": None,
        "deploy_type": None,
        "backend_port": None,
        "admin_credentials": None,
        "created_at": now,
        "updated_at": now
    }
    await db.deployments.insert_one(deployment)
    
    # Start deployment in background
    background_tasks.add_task(run_deployment, deployment_id, vps, deployment)
    
    return DeploymentResponse(
        id=deployment_id, vps_id=data.vps_id, repo_url=data.repo_url, branch=data.branch,
        project_name=data.project_name, port=data.port, status=DeployStatus.PENDING,
        logs=[], created_at=now, updated_at=now
    )

@api_router.get("/deployments", response_model=List[DeploymentResponse])
async def list_deployments(user: dict = Depends(get_current_user)):
    deployments = await db.deployments.find(
        {"user_id": user["id"]}, 
        {"_id": 0, "github_token_encrypted": 0, "env_vars": 0}
    ).sort("created_at", -1).to_list(100)
    return [DeploymentResponse(**d) for d in deployments]

@api_router.get("/deployments/{deployment_id}", response_model=DeploymentResponse)
async def get_deployment(deployment_id: str, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one(
        {"id": deployment_id, "user_id": user["id"]},
        {"_id": 0, "github_token_encrypted": 0}
    )
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return DeploymentResponse(**deployment)

@api_router.post("/deployments/{deployment_id}/redeploy", response_model=DeploymentResponse)
async def redeploy(deployment_id: str, background_tasks: BackgroundTasks, user: dict = Depends(get_current_user)):
    """
    Redeploy an existing deployment.
    This preserves the MongoDB database and only rebuilds frontend/backend containers.
    """
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    await db.deployments.update_one({"id": deployment_id}, {"$set": {"status": DeployStatus.PENDING, "logs": []}})
    # Pass is_redeploy=True to preserve MongoDB data
    background_tasks.add_task(run_deployment, deployment_id, vps, deployment, is_redeploy=True)
    
    deployment["status"] = DeployStatus.PENDING
    deployment["logs"] = []
    return DeploymentResponse(**{k: v for k, v in deployment.items() if k != "github_token_encrypted"})

@api_router.post("/deployments/{deployment_id}/stop")
async def stop_deployment(deployment_id: str, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    try:
        ssh = get_ssh_client(vps)
        project_name = deployment['project_name']
        
        # Stop all containers for this project (fullstack support)
        containers_to_stop = [
            f"deploy_{project_name}",      # Single container deployment
            f"frontend_{project_name}",    # Fullstack frontend
            f"backend_{project_name}",     # Fullstack backend
        ]
        
        for container in containers_to_stop:
            ssh.exec_command(f"docker stop {container} 2>/dev/null")
        
        ssh.close()
        
        await update_deployment_status(deployment_id, DeployStatus.STOPPED)
        await add_deployment_log(deployment_id, "All containers stopped", "info")
        
        return {"message": "Containers stopped"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.delete("/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Try to stop and remove ALL containers (frontend, backend, mongodb)
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if vps:
        try:
            ssh = get_ssh_client(vps)
            project_name = deployment['project_name']
            
            # List of all possible container names for this project
            containers_to_remove = [
                f"deploy_{project_name}",      # Single container deployment
                f"frontend_{project_name}",    # Fullstack frontend
                f"backend_{project_name}",     # Fullstack backend
                f"mongodb_{project_name}",     # MongoDB container
            ]
            
            # Stop and remove all containers
            for container in containers_to_remove:
                ssh.exec_command(f"docker stop {container} 2>/dev/null; docker rm {container} 2>/dev/null")
            
            # Also remove the Docker network if it exists
            network_name = f"network_{project_name}"
            ssh.exec_command(f"docker network rm {network_name} 2>/dev/null")
            
            # Optionally remove deployment directory (commented out for safety)
            # ssh.exec_command(f"rm -rf /opt/deployments/{project_name}")
            
            ssh.close()
        except:
            pass
    
    await db.deployments.delete_one({"id": deployment_id})
    return {"message": "Deployment deleted"}

# ============ DOMAIN ROUTES ============

@api_router.post("/deployments/{deployment_id}/domain")
async def configure_domain(deployment_id: str, config: DomainConfig, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    domain = config.domain
    port = deployment["port"]
    backend_port = deployment.get("backend_port", port + 1000)
    project_name = deployment["project_name"]
    deploy_type = deployment.get("deploy_type", "static")
    
    try:
        ssh = get_ssh_client(vps)
        
        # Detect web server (Apache or Nginx)
        stdin, stdout, stderr = ssh.exec_command("which apache2 apachectl 2>/dev/null | head -1")
        has_apache = bool(stdout.read().decode().strip())
        
        stdin, stdout, stderr = ssh.exec_command("which nginx 2>/dev/null")
        has_nginx = bool(stdout.read().decode().strip())
        
        # Check which one is actually running/listening on port 80
        stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep ':80' | head -1")
        port_80_info = stdout.read().decode()
        
        use_apache = "apache" in port_80_info.lower() or (has_apache and not has_nginx)
        web_server = "apache" if use_apache else "nginx"
        
        await add_deployment_log(deployment_id, f"Detected web server: {web_server.upper()}", "info")
        
        sftp = ssh.open_sftp()
        
        if use_apache:
            # ============ APACHE CONFIGURATION ============
            if deploy_type == "fullstack":
                apache_config = f"""<VirtualHost *:80>
    ServerName {domain}
    
    # Redirect to HTTPS
    RewriteEngine On
    RewriteCond %{{HTTPS}} off
    RewriteRule ^(.*)$ https://%{{HTTP_HOST}}%{{REQUEST_URI}} [L,R=301]
</VirtualHost>
"""
            else:
                apache_config = f"""<VirtualHost *:80>
    ServerName {domain}
    
    ProxyPreserveHost On
    ProxyRequests Off
    
    ProxyPass / http://127.0.0.1:{port}/
    ProxyPassReverse / http://127.0.0.1:{port}/
</VirtualHost>
"""
            
            apache_path = f"/etc/apache2/sites-available/{domain}.conf"
            with sftp.file(apache_path, "w") as f:
                f.write(apache_config)
            
            # Enable required modules and site
            ssh.exec_command("a2enmod proxy proxy_http rewrite headers 2>/dev/null")
            ssh.exec_command(f"a2ensite {domain}.conf 2>/dev/null")
            ssh.exec_command("apache2ctl configtest && systemctl reload apache2")
            
        else:
            # ============ NGINX CONFIGURATION ============
            if deploy_type == "fullstack":
                nginx_config = f"""server {{
    listen 80;
    server_name {domain};
    
    location /api {{
        proxy_pass http://localhost:{backend_port}/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
    
    location / {{
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
            else:
                nginx_config = f"""server {{
    listen 80;
    server_name {domain};
    
    location / {{
        proxy_pass http://localhost:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }}
}}
"""
            
            nginx_path = f"/etc/nginx/sites-available/{project_name}"
            with sftp.file(nginx_path, "w") as f:
                f.write(nginx_config)
            
            ssh.exec_command(f"ln -sf {nginx_path} /etc/nginx/sites-enabled/{project_name}")
            ssh.exec_command("nginx -t && systemctl reload nginx")
        
        sftp.close()
        ssh.close()
        
        await db.deployments.update_one({"id": deployment_id}, {"$set": {"domain": domain, "web_server": web_server}})
        await add_deployment_log(deployment_id, f"Domain {domain} configured successfully", "success")
        
        return {
            "message": "Domain configured",
            "domain": domain,
            "web_server": web_server,
            "vps_host": vps["host"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure domain: {str(e)}")


@api_router.post("/deployments/{deployment_id}/ssl")
async def configure_ssl(deployment_id: str, user: dict = Depends(get_current_user)):
    """Configure SSL/HTTPS using Let's Encrypt certbot (supports both Apache and Nginx)"""
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if not deployment.get("domain"):
        raise HTTPException(status_code=400, detail="Configure um domínio primeiro antes de ativar HTTPS")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    domain = deployment["domain"]
    port = deployment["port"]
    backend_port = deployment.get("backend_port", port + 1000)
    deploy_type = deployment.get("deploy_type", "static")
    web_server = deployment.get("web_server", "nginx")
    
    try:
        ssh = get_ssh_client(vps)
        
        # Auto-detect web server if not stored
        if not deployment.get("web_server"):
            stdin, stdout, stderr = ssh.exec_command("netstat -tlnp 2>/dev/null | grep ':80' | head -1")
            port_80_info = stdout.read().decode()
            web_server = "apache" if "apache" in port_80_info.lower() else "nginx"
        
        await add_deployment_log(deployment_id, f"Configuring SSL with {web_server.upper()}...", "info")
        
        # Check if certbot is installed
        stdin, stdout, stderr = ssh.exec_command("which certbot")
        if not stdout.read().decode().strip():
            await add_deployment_log(deployment_id, "Installing certbot...", "info")
            if web_server == "apache":
                ssh.exec_command("apt-get update && apt-get install -y certbot python3-certbot-apache")
            else:
                ssh.exec_command("apt-get update && apt-get install -y certbot python3-certbot-nginx")
            await asyncio.sleep(10)
        
        await add_deployment_log(deployment_id, f"Configuring SSL for {domain}...", "info")
        
        if web_server == "apache":
            # ============ APACHE SSL ============
            # Run certbot for Apache
            stdin, stdout, stderr = ssh.exec_command(f"certbot --apache -d {domain} --non-interactive --agree-tos --email admin@{domain} --redirect 2>&1")
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            # If certbot succeeded, update the SSL config to include proper proxy settings
            if "Congratulations" in output or "Successfully" in output or "Certificate not yet due for renewal" in output:
                sftp = ssh.open_sftp()
                
                # Create/update SSL config with full proxy settings
                if deploy_type == "fullstack":
                    ssl_config = f"""<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName {domain}

    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"
    Header always set Referrer-Policy "strict-origin-when-cross-origin"

    ProxyPreserveHost On
    ProxyRequests Off

    # Backend API (must come before /)
    ProxyPass /api http://127.0.0.1:{backend_port}/api
    ProxyPassReverse /api http://127.0.0.1:{backend_port}/api

    # Frontend
    ProxyPass / http://127.0.0.1:{port}/
    ProxyPassReverse / http://127.0.0.1:{port}/

    SSLCertificateFile /etc/letsencrypt/live/{domain}/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/{domain}/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf
</VirtualHost>
</IfModule>
"""
                else:
                    ssl_config = f"""<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName {domain}

    # Security Headers
    Header always set X-Frame-Options "SAMEORIGIN"
    Header always set X-Content-Type-Options "nosniff"
    Header always set X-XSS-Protection "1; mode=block"

    ProxyPreserveHost On
    ProxyRequests Off

    ProxyPass / http://127.0.0.1:{port}/
    ProxyPassReverse / http://127.0.0.1:{port}/

    SSLCertificateFile /etc/letsencrypt/live/{domain}/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/{domain}/privkey.pem
    Include /etc/letsencrypt/options-ssl-apache.conf
</VirtualHost>
</IfModule>
"""
                
                ssl_path = f"/etc/apache2/sites-available/{domain}-le-ssl.conf"
                with sftp.file(ssl_path, "w") as f:
                    f.write(ssl_config)
                sftp.close()
                
                # Enable modules and reload
                ssh.exec_command("a2enmod ssl headers proxy proxy_http 2>/dev/null")
                ssh.exec_command(f"a2ensite {domain}-le-ssl.conf 2>/dev/null")
                ssh.exec_command("apache2ctl configtest && systemctl reload apache2")
                
                await add_deployment_log(deployment_id, f"SSL/HTTPS configured successfully for {domain}", "success")
                ssh.close()
                return {"message": "SSL configured successfully", "domain": domain, "https_url": f"https://{domain}"}
        else:
            # ============ NGINX SSL ============
            stdin, stdout, stderr = ssh.exec_command(f"certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain} --redirect 2>&1")
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            if "Congratulations" in output or "Successfully" in output or "Certificate not yet due for renewal" in output:
                await add_deployment_log(deployment_id, f"SSL/HTTPS configured successfully for {domain}", "success")
                ssh.close()
                return {"message": "SSL configured successfully", "domain": domain, "https_url": f"https://{domain}"}
        
        ssh.close()
        
        await add_deployment_log(deployment_id, f"SSL configuration output: {output}", "warning")
        return {"message": "SSL configuration attempted", "output": output, "error": error}
            
    except Exception as e:
        await add_deployment_log(deployment_id, f"SSL configuration failed: {str(e)}", "error")
        raise HTTPException(status_code=500, detail=f"Failed to configure SSL: {str(e)}")

@api_router.delete("/deployments/{deployment_id}/domain")
async def remove_domain(deployment_id: str, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if vps and deployment.get("domain"):
        try:
            ssh = get_ssh_client(vps)
            project_name = deployment["project_name"]
            domain = deployment["domain"]
            web_server = deployment.get("web_server", "nginx")
            
            if web_server == "apache":
                # Remove Apache configs
                ssh.exec_command(f"a2dissite {domain}.conf {domain}-le-ssl.conf 2>/dev/null")
                ssh.exec_command(f"rm -f /etc/apache2/sites-available/{domain}.conf /etc/apache2/sites-available/{domain}-le-ssl.conf")
                ssh.exec_command("systemctl reload apache2")
            else:
                # Remove Nginx configs
                ssh.exec_command(f"rm -f /etc/nginx/sites-enabled/{project_name} /etc/nginx/sites-available/{project_name}")
                ssh.exec_command("systemctl reload nginx")
            
            ssh.close()
        except:
            pass
    
    await db.deployments.update_one({"id": deployment_id}, {"$set": {"domain": None, "web_server": None}})
    return {"message": "Domain removed"}

# ============ LIVE LOGS ============

@api_router.get("/deployments/{deployment_id}/logs")
async def get_container_logs(deployment_id: str, user: dict = Depends(get_current_user)):
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if deployment["status"] != DeployStatus.RUNNING:
        return {"logs": deployment.get("logs", []), "container_logs": []}
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        return {"logs": deployment.get("logs", []), "container_logs": []}
    
    try:
        ssh = get_ssh_client(vps)
        container_name = f"deploy_{deployment['project_name']}"
        stdin, stdout, stderr = ssh.exec_command(f"docker logs --tail 100 {container_name} 2>&1")
        container_logs = stdout.read().decode().split("\n")
        ssh.close()
        
        return {"logs": deployment.get("logs", []), "container_logs": container_logs}
    except Exception as e:
        return {"logs": deployment.get("logs", []), "container_logs": [], "error": str(e)}

# ============ HEALTH CHECK ============

@api_router.get("/")
async def root():
    return {"message": "Deploy Git to VPS API", "status": "running"}

@api_router.get("/health")
async def health():
    return {"status": "healthy"}

# Include router and setup middleware
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
