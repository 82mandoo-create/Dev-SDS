from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.pc import PCStatus, SecurityLevel


class PCAssetBase(BaseModel):
    asset_tag: str
    hostname: Optional[str] = None
    computer_name: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None


class PCAssetCreate(PCAssetBase):
    assigned_employee_id: Optional[int] = None


class PCAssetUpdate(BaseModel):
    hostname: Optional[str] = None
    computer_name: Optional[str] = None
    assigned_employee_id: Optional[int] = None
    status: Optional[PCStatus] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    antivirus_installed: Optional[bool] = None
    firewall_enabled: Optional[bool] = None
    disk_encrypted: Optional[bool] = None


class PCAssetResponse(PCAssetBase):
    id: int
    status: PCStatus
    security_level: SecurityLevel
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    cpu_info: Optional[str] = None
    ram_gb: Optional[float] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    agent_version: Optional[str] = None
    is_online: bool = False
    last_heartbeat: Optional[datetime] = None
    assigned_employee_id: Optional[int] = None
    antivirus_installed: bool = False
    antivirus_name: Optional[str] = None
    firewall_enabled: bool = False
    disk_encrypted: bool = False
    windows_defender: bool = False
    security_score: int = 0
    purchase_date: Optional[datetime] = None
    warranty_expiry: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AgentRegisterRequest(BaseModel):
    agent_secret: str
    hostname: str
    computer_name: str
    serial_number: Optional[str] = None
    mac_address: Optional[str] = None
    os_name: Optional[str] = None
    os_version: Optional[str] = None
    os_build: Optional[str] = None
    os_architecture: Optional[str] = None
    cpu_info: Optional[str] = None
    ram_gb: Optional[float] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None


class AgentHeartbeatRequest(BaseModel):
    agent_token: str
    ip_address: Optional[str] = None
    is_online: bool = True
    cpu_usage: Optional[float] = None
    ram_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    antivirus_installed: Optional[bool] = None
    firewall_enabled: Optional[bool] = None
    disk_encrypted: Optional[bool] = None
    windows_defender: Optional[bool] = None
    security_score: Optional[int] = None


class AgentActivityReport(BaseModel):
    agent_token: str
    activities: List[Dict[str, Any]]


class AgentAppReport(BaseModel):
    agent_token: str
    applications: List[Dict[str, Any]]


class PCActivityResponse(BaseModel):
    id: int
    pc_asset_id: int
    activity_type: str
    user_account: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SecurityEventResponse(BaseModel):
    id: int
    pc_asset_id: int
    event_type: str
    severity: SecurityLevel
    title: str
    description: Optional[str] = None
    is_resolved: bool = False
    occurred_at: datetime
    
    class Config:
        from_attributes = True
