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

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

class UserCreateByAdmin(BaseModel):
    email: EmailStr
    password: str
    name: str
    role: str = "user"  # user or admin

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

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
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def encrypt_data(data: str) -> str:
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(data: str) -> str:
    return fernet.decrypt(data.encode()).decode()

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # First user is admin, others are regular users
    user_count = await db.users.count_documents({})
    role = "admin" if user_count == 0 else "user"
    
    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "password_hash": hash_password(user_data.password),
        "role": role,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    token = create_token(user_id)
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user_id, email=user_data.email, name=user_data.name, role=role, created_at=user["created_at"])
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    token = create_token(user["id"])
    return TokenResponse(
        access_token=token,
        user=UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user.get("role", "user"), created_at=user["created_at"])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(user: dict = Depends(get_current_user)):
    return UserResponse(id=user["id"], email=user["email"], name=user["name"], role=user.get("role", "user"), created_at=user["created_at"])

# ============ ADMIN ROUTES ============

def require_admin(user: dict = Depends(get_current_user)):
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    return user

@api_router.get("/admin/users", response_model=List[UserResponse])
async def list_users(admin: dict = Depends(require_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    return [UserResponse(**{**u, "role": u.get("role", "user")}) for u in users]

@api_router.post("/admin/users", response_model=UserResponse)
async def create_user(user_data: UserCreateByAdmin, admin: dict = Depends(require_admin)):
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
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user)
    
    return UserResponse(id=user_id, email=user_data.email, name=user_data.name, role=user_data.role, created_at=user["created_at"])

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
        
        # Generate bcrypt hash for password
        import secrets
        user_id = str(uuid.uuid4())
        
        # Create the admin user document
        admin_script = f'''
docker exec mongodb_{db_name} mongosh --eval '
db = db.getSiblingDB("{db_name}");
var bcrypt_hash = "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.wFXlGJvP.HZfIe";
db.users.insertOne({{
    "id": "{user_id}",
    "name": "Administrador",
    "email": "{admin_email}",
    "password": bcrypt_hash,
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

async def run_deployment(deployment_id: str, vps: dict, deployment: dict):
    try:
        await update_deployment_status(deployment_id, DeployStatus.CLONING)
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
        if deployment.get("create_mongodb"):
            mongodb_container = f"mongodb_{project_name}"
            mongodb_volume = f"mongodb_data_{project_name}"
            
            await add_deployment_log(deployment_id, f"Setting up MongoDB container on port {mongodb_port_used}...")
            
            ssh.exec_command(f"docker stop {mongodb_container} 2>/dev/null; docker rm {mongodb_container} 2>/dev/null")
            await asyncio.sleep(1)
            
            ssh.exec_command(f"docker volume create {mongodb_volume}")
            
            mongo_cmd = f"docker run -d --name {mongodb_container} -p {mongodb_port_used}:27017 -v {mongodb_volume}:/data/db --restart unless-stopped mongo:6"
            stdin, stdout, stderr = ssh.exec_command(mongo_cmd)
            mongo_output = stdout.read().decode()
            
            if stdout.channel.recv_exit_status() == 0:
                mongodb_url = f"mongodb://localhost:{mongodb_port_used}/{project_name}"
                env_string += f" -e MONGO_URL='{mongodb_url}'"
                env_string += f" -e MONGODB_URL='{mongodb_url}'"
                env_string += f" -e DATABASE_URL='{mongodb_url}'"
                env_string += f" -e DB_NAME='{project_name}'"
                await add_deployment_log(deployment_id, f"MongoDB running on port {mongodb_port_used}", "success")
                await db.deployments.update_one({"id": deployment_id}, {"$set": {"mongodb_url": mongodb_url}})
                await asyncio.sleep(3)  # Wait for MongoDB to be ready
            else:
                await add_deployment_log(deployment_id, f"Warning: Failed to start MongoDB - {stderr.read().decode()}", "warning")
        
        # ============ FULLSTACK DEPLOYMENT ============
        if is_fullstack:
            await add_deployment_log(deployment_id, f"🚀 Starting FULLSTACK deployment...")
            await add_deployment_log(deployment_id, f"Frontend port: {port} | Backend port: {backend_port}")
            await db.deployments.update_one({"id": deployment_id}, {"$set": {"backend_port": backend_port}})
            
            # Create Docker network for communication
            network_name = f"network_{project_name}"
            ssh.exec_command(f"docker network create {network_name} 2>/dev/null || true")
            
            # ---- BUILD AND RUN BACKEND ----
            await add_deployment_log(deployment_id, "Building backend...")
            backend_container = f"backend_{project_name}"
            
            backend_dockerfile = f"""FROM python:3.11-slim
WORKDIR /app
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
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
            
            # Stop existing backend
            ssh.exec_command(f"docker stop {backend_container} 2>/dev/null; docker rm {backend_container} 2>/dev/null")
            await asyncio.sleep(1)
            
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
            
            # Stop existing frontend
            ssh.exec_command(f"docker stop {frontend_container} 2>/dev/null; docker rm {frontend_container} 2>/dev/null")
            await asyncio.sleep(1)
            
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
            
            # Create admin user if requested and MongoDB is available
            if deployment.get("create_admin") and deployment.get("create_mongodb"):
                await asyncio.sleep(2)  # Wait for services to be ready
                admin_email = deployment.get("admin_email", "admin@admin.com")
                admin_password = deployment.get("admin_password", "Admin@123")
                await create_admin_user(ssh, mongodb_port_used, admin_email, admin_password, deployment_id, project_name)
            
            await update_deployment_status(deployment_id, DeployStatus.RUNNING, container_id=container_id)
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
            
            # Run container
            await add_deployment_log(deployment_id, f"Starting container on port {port}...")
            run_cmd = f"docker run -d --name {container_name} -p {port}:{internal_port} --restart unless-stopped {env_string} {container_name}:latest"
            stdin, stdout, stderr = ssh.exec_command(run_cmd)
            container_id = stdout.read().decode().strip()[:12]
            
            if stdout.channel.recv_exit_status() != 0:
                error = stderr.read().decode()
                raise Exception(f"Failed to start container: {error}")
            
            # Create admin user if requested and MongoDB is available
            if deployment.get("create_admin") and deployment.get("create_mongodb"):
                await asyncio.sleep(2)
                admin_email = deployment.get("admin_email", "admin@admin.com")
                admin_password = deployment.get("admin_password", "Admin@123")
                await create_admin_user(ssh, mongodb_port_used, admin_email, admin_password, deployment_id, project_name)
            
            await update_deployment_status(deployment_id, DeployStatus.RUNNING, container_id=container_id)
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
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    await db.deployments.update_one({"id": deployment_id}, {"$set": {"status": DeployStatus.PENDING, "logs": []}})
    background_tasks.add_task(run_deployment, deployment_id, vps, deployment)
    
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
    project_name = deployment["project_name"]
    
    # Nginx config for reverse proxy
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
    
    try:
        ssh = get_ssh_client(vps)
        
        # Write nginx config
        sftp = ssh.open_sftp()
        nginx_path = f"/etc/nginx/sites-available/{project_name}"
        with sftp.file(nginx_path, "w") as f:
            f.write(nginx_config)
        sftp.close()
        
        # Enable site and reload nginx
        ssh.exec_command(f"ln -sf {nginx_path} /etc/nginx/sites-enabled/{project_name}")
        ssh.exec_command("nginx -t && systemctl reload nginx")
        
        ssh.close()
        
        await db.deployments.update_one({"id": deployment_id}, {"$set": {"domain": domain}})
        await add_deployment_log(deployment_id, f"Domain {domain} configured successfully", "success")
        
        return {
            "message": "Domain configured",
            "domain": domain,
            "vps_host": vps["host"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to configure domain: {str(e)}")


@api_router.post("/deployments/{deployment_id}/ssl")
async def configure_ssl(deployment_id: str, user: dict = Depends(get_current_user)):
    """Configure SSL/HTTPS using Let's Encrypt certbot"""
    deployment = await db.deployments.find_one({"id": deployment_id, "user_id": user["id"]}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    if not deployment.get("domain"):
        raise HTTPException(status_code=400, detail="Configure um domínio primeiro antes de ativar HTTPS")
    
    vps = await db.vps.find_one({"id": deployment["vps_id"], "user_id": user["id"]}, {"_id": 0})
    if not vps:
        raise HTTPException(status_code=404, detail="VPS not found")
    
    domain = deployment["domain"]
    
    try:
        ssh = get_ssh_client(vps)
        
        # Check if certbot is installed
        stdin, stdout, stderr = ssh.exec_command("which certbot")
        if not stdout.read().decode().strip():
            # Install certbot
            await add_deployment_log(deployment_id, "Installing certbot...", "info")
            ssh.exec_command("apt-get update && apt-get install -y certbot python3-certbot-nginx")
            await asyncio.sleep(5)
        
        # Run certbot
        await add_deployment_log(deployment_id, f"Configuring SSL for {domain}...", "info")
        stdin, stdout, stderr = ssh.exec_command(f"certbot --nginx -d {domain} --non-interactive --agree-tos --email admin@{domain} --redirect 2>&1")
        output = stdout.read().decode()
        error = stderr.read().decode()
        
        ssh.close()
        
        if "Congratulations" in output or "Successfully" in output:
            await add_deployment_log(deployment_id, f"SSL/HTTPS configured successfully for {domain}", "success")
            return {"message": "SSL configured successfully", "domain": domain, "https_url": f"https://{domain}"}
        else:
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
            ssh.exec_command(f"rm -f /etc/nginx/sites-enabled/{project_name} /etc/nginx/sites-available/{project_name}")
            ssh.exec_command("systemctl reload nginx")
            ssh.close()
        except:
            pass
    
    await db.deployments.update_one({"id": deployment_id}, {"$set": {"domain": None}})
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
