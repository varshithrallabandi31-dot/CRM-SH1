"""
Database Models and Engine Setup for Cold Outreach CRM
"""
import uuid
from datetime import datetime
from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship, create_engine, Session, JSON
from sqlalchemy import Column, String, Index, DateTime, select, func, Text
from sqlalchemy.dialects.postgresql import JSONB
import os
from dotenv import load_dotenv

load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

# Create engine with SSL mode for Neon PostgreSQL
engine = create_engine(
    DATABASE_URL,
    echo=False,  # Set to False in production
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)


class User(SQLModel, table=True):
    """
    User model for authentication and role management
    """
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    password: str
    name: Optional[str] = None
    role: str = Field(default="Client") # Admin, Employee, Client
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    profile: Optional["ClientProfile"] = Relationship(back_populates="user")
    activities: List["ActivityLog"] = Relationship(back_populates="user")


class Project(SQLModel, table=True):
    """
    Dedicated model for managing client projects, team assignments, and progress.
    """
    __tablename__ = "projects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    description: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="Planning") # Planning, Active, Completed, Hold
    progress: int = Field(default=0) # 0-100
    
    # Team assignments stored as JSONB list of IDs for flexibility
    # In a larger app, these would be junction tables
    employeeIds: Optional[List[int]] = Field(default_factory=list, sa_column=Column(JSONB))
    internIds: Optional[List[int]] = Field(default_factory=list, sa_column=Column(JSONB))
    clientIds: Optional[List[int]] = Field(default_factory=list, sa_column=Column(JSONB))
    
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    updatedAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    remarks: List["Remark"] = Relationship(back_populates="project")


class ClientProfile(SQLModel, table=True):
    """
    Detailed profile for clients
    """
    __tablename__ = "client_profiles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    userId: Optional[int] = Field(default=None, foreign_key="users.id")
    projectId: Optional[int] = Field(default=None, foreign_key="projects.id")
    companyName: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = Field(default="Active") # Active, Hold, Pending
    customFields: Optional[dict] = Field(default_factory=dict, sa_column=Column(JSONB))
    assignedEmployeeId: Optional[int] = None
    projectName: Optional[str] = None
    gmbName: Optional[str] = None
    seoStrategy: Optional[str] = None
    tagline: Optional[str] = None
    targetKeywords: Optional[List[str]] = Field(default_factory=list, sa_column=Column(JSONB))
    websiteUrl: Optional[str] = None
    recommended_services: Optional[str] = Field(default=None, max_length=1000)
    nextMilestone: Optional[str] = None
    nextMilestoneDate: Optional[str] = None
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="profile")
    remarks: List["Remark"] = Relationship(back_populates="client")
    documents: List["Document"] = Relationship(back_populates="client")


class Remark(SQLModel, table=True):
    """
    Internal or client-facing remarks/comments
    """
    __tablename__ = "remarks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    content: str = Field(sa_column=Column(Text))
    authorId: Optional[int] = Field(default=None, foreign_key="users.id")
    clientId: Optional[int] = Field(default=None, foreign_key="client_profiles.id")
    projectId: Optional[int] = Field(default=None, foreign_key="projects.id")
    isInternal: bool = Field(default=True)
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Optional[ClientProfile] = Relationship(back_populates="remarks")
    project: Optional[Project] = Relationship(back_populates="remarks")


class Document(SQLModel, table=True):
    """
    Documents and OCR results
    """
    __tablename__ = "documents"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    fileUrl: str
    ocrText: Optional[str] = Field(default=None, sa_column=Column(Text))
    status: str = Field(default="Pending")
    uploaderId: Optional[int] = Field(default=None, foreign_key="users.id")
    clientId: Optional[int] = Field(default=None, foreign_key="client_profiles.id")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    client: Optional[ClientProfile] = Relationship(back_populates="documents")


class ActivityLog(SQLModel, table=True):
    """
    Logs of user actions and manual client activities
    """
    __tablename__ = "activity_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    userId: Optional[int] = Field(default=None, foreign_key="users.id")
    clientId: Optional[int] = Field(default=None, foreign_key="client_profiles.id")
    action: str # e.g., "Manual Activity", "Login", "Profile Update"
    method: Optional[str] = None # Email, Phone, In-person, WhatsApp, Website
    content: Optional[str] = Field(default=None, sa_column=Column(Text))
    details: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    user: Optional[User] = Relationship(back_populates="activities")
    client: Optional[ClientProfile] = Relationship()


class Company(SQLModel, table=True):
    """
    Company model - stores prospect information
    """
    __tablename__ = "companies"
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    company_name: str = Field(max_length=255)
    website_url: str = Field(
        max_length=500,
        sa_column=Column(String(500), unique=True, index=True, nullable=False)
    )
    primary_email: str = Field(max_length=255)
    email_sender: str = Field(default="padilla@dapros.com", max_length=255)
    email_sent_status: bool = Field(default=False)
    recommended_services: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationship to EmailLog
    email_logs: List["EmailLog"] = Relationship(back_populates="company")


class EmailLog(SQLModel, table=True):
    """
    EmailLog model - tracks all sent emails for rate limiting
    """
    __tablename__ = "email_logs"
    __table_args__ = (
        Index('ix_email_logs_sender_sent_at', 'sender_email', 'sent_at'),
    )
    
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        primary_key=True
    )
    company_id: uuid.UUID = Field(foreign_key="companies.id")
    sender_email: str = Field(max_length=255)
    sent_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False
    )
    
    # Relationship back to Company
    company: Optional[Company] = Relationship(back_populates="email_logs")


def create_db_and_tables():
    """
    Create all database tables (drops existing tables first to ensure schema matches)
    """
    # Create all tables if they don't exist
    SQLModel.metadata.create_all(engine)
    
    # Run migrations
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS \"nextMilestone\" VARCHAR(255)"))
            conn.execute(text("ALTER TABLE client_profiles ADD COLUMN IF NOT EXISTS \"nextMilestoneDate\" VARCHAR(255)"))
            conn.commit()
    except Exception as e:
        print(f"Migration note: {e}")


def get_session():
    """
    Dependency to get database session
    """
    with Session(engine) as session:
        yield session


if __name__ == "__main__":
    print("Creating database tables...")
    create_db_and_tables()
    print("Database tables created successfully!")
