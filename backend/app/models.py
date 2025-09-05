from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Union, Dict, Any
from datetime import datetime, timezone, timedelta
from enum import Enum

# New Teacher-Classroom-Student Models
class SessionType(str, Enum):
    FORENOON = "forenoon"
    AFTERNOON = "afternoon"

class Classroom(BaseModel):
    classroom_id: str = Field(..., description="Unique classroom identifier")
    name: str = Field(..., description="Classroom name (e.g., Class 8A)")
    hashcode: str = Field(..., description="5-digit hashcode for students to join")
    students: List[str] = Field(default_factory=list, description="List of student IDs")
    demo_projects: List[str] = Field(default_factory=list, description="List of demo project IDs")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = Field(True, description="Whether classroom is active")

class Teacher(BaseModel):
    teacher_id: str = Field(..., description="Unique teacher identifier")
    name: str = Field(..., description="Teacher's full name")
    school_name: str = Field(..., description="School name")
    date_of_training: str = Field(..., description="Training date (YYYY-MM-DD)")
    session: SessionType = Field(..., description="Training session time")
    classrooms: List[Classroom] = Field(default_factory=list, description="List of classrooms")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = Field(True, description="Whether teacher account is active")

class TeacherCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    school_name: str = Field(..., min_length=1, max_length=200)
    date_of_training: str = Field(..., description="Training date (YYYY-MM-DD)")
    session: SessionType

class ClassroomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Classroom name")

class Student(BaseModel):
    student_id: str = Field(..., description="Unique student identifier")
    name: str = Field(..., description="Student's full name")
    teacher_id: str = Field(..., description="Teacher ID this student belongs to")
    classroom_id: str = Field(..., description="Classroom ID this student belongs to")
    hashcode: str = Field(..., description="Hashcode used to join")
    projects: List[dict] = Field(default_factory=list, description="List of student's projects")
    accessible_demos: List[str] = Field(default_factory=list, description="List of accessible demo project IDs")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = Field(True, description="Whether student account is active")

class StudentJoin(BaseModel):
    hashcode: str = Field(..., min_length=5, max_length=5, description="5-digit hashcode")
    name: str = Field(..., min_length=1, max_length=100, description="Student's name")

class TeacherResponse(BaseModel):
    success: bool = True
    data: Teacher

class TeacherListResponse(BaseModel):
    success: bool = True
    data: List[Teacher]

class ClassroomResponse(BaseModel):
    success: bool = True
    data: Classroom

class StudentResponse(BaseModel):
    success: bool = True
    data: Student

class StudentListResponse(BaseModel):
    success: bool = True
    data: List[Student]

class TeacherDashboardResponse(BaseModel):
    success: bool = True
    data: dict


class ProjectType(str, Enum):
    TEXT_RECOGNITION = "text-recognition"
    IMAGE_RECOGNITION = "image-recognition-teachable-machine"
    CLASSIFICATION = "classification"
    REGRESSION = "regression"
    CUSTOM = "custom"


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    TRAINING = "training"
    TRAINED = "trained"
    TESTING = "testing"
    FAILED = "failed"


class TextExample(BaseModel):
    text: str = Field(..., description="Text example")
    label: str = Field(..., description="Label for this example")
    addedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Dataset(BaseModel):
    filename: str = Field("", description="Name of the dataset file")
    size: int = Field(0, description="File size in bytes")
    records: int = Field(0, description="Number of records in the dataset")
    uploadedAt: Optional[datetime] = Field(None, description="When the dataset was uploaded")
    gcsPath: str = Field("", description="GCS path to the dataset file")
    examples: List[TextExample] = Field(default_factory=list, description="Text examples")
    labels: List[str] = Field(default_factory=list, description="Unique labels in dataset")


class TrainedModel(BaseModel):
    filename: str = Field("", description="Name of the model file")
    accuracy: Optional[float] = Field(None, description="Model accuracy score")
    loss: Optional[float] = Field(None, description="Model loss value")
    trainedAt: Optional[datetime] = Field(None, description="When the model was trained")
    gcsPath: str = Field("", description="GCS path to the model file")
    labels: List[str] = Field(default_factory=list, description="Labels the model can predict")
    modelType: str = Field("logistic_regression", description="Type of model used")
    endpointUrl: str = Field("", description="URL for prediction endpoint")


class ProjectConfig(BaseModel):
    epochs: int = Field(100, ge=1, le=10000, description="Number of training epochs")
    batchSize: int = Field(32, ge=1, le=10000, description="Training batch size")
    learningRate: float = Field(0.001, gt=0, le=1, description="Learning rate")
    validationSplit: float = Field(0.2, gt=0, lt=1, description="Validation split ratio")


class Project(BaseModel):
    id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    description: str = Field("", max_length=500, description="Project description")
    type: ProjectType = Field(ProjectType.TEXT_RECOGNITION, description="Project type")
    status: ProjectStatus = Field(ProjectStatus.DRAFT, description="Current project status")
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Creation timestamp")
    updatedAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    createdBy: str = Field("", description="User who created the project")
    
    # Teacher-Classroom-Student linking
    teacher_id: str = Field("", description="Teacher ID this project belongs to")
    classroom_id: str = Field("", description="Classroom ID this project belongs to")
    student_id: str = Field("", description="Student ID who created this project")
    
    # School and class information (legacy, can be derived from teacher/classroom)
    schoolId: str = Field("", description="School identifier")
    classId: str = Field("", description="Class identifier")
    
    # Dataset information
    dataset: Dataset = Field(default_factory=lambda: Dataset(), description="Primary dataset")
    datasets: List[Dataset] = Field(default_factory=list, description="List of all datasets")
    
    # Model information
    model: TrainedModel = Field(default_factory=lambda: TrainedModel(), description="Trained model details")
    
    # Training configuration (optional for image-recognition-teachable-machine projects)
    config: Optional[ProjectConfig] = Field(None, description="Training configuration")
    
    # Teachable Machine integration (for image recognition projects)
    teachable_machine_link: Optional[str] = Field(None, description="Teachable Machine model link for image recognition projects")
    
    # Training history and job management
    trainingHistory: List[dict] = Field(default_factory=list, description="Training history logs")
    currentJobId: Optional[str] = Field(None, description="Current training job ID")
    
    # Lifecycle management
    expiryTimestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=timezone.utc) + timedelta(days=7),
        description="Project expiry timestamp (default 7 days)"
    )
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Project tags")
    notes: str = Field("", max_length=1000, description="Additional notes")


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str = Field("", max_length=500)
    type: ProjectType = Field(ProjectType.TEXT_RECOGNITION)
    createdBy: str = Field("")
    teacher_id: str = Field("", description="Teacher ID this project belongs to")
    classroom_id: str = Field("", description="Classroom ID this project belongs to")
    student_id: str = Field("", description="Student ID who created this project")
    tags: List[str] = Field(default_factory=list)
    notes: str = Field("", max_length=1000)
    config: Optional[ProjectConfig] = None
    teachable_machine_link: Optional[str] = Field(None, description="Teachable Machine model link for image recognition projects")


class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    type: Optional[ProjectType] = None
    status: Optional[ProjectStatus] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=1000)
    config: Optional[ProjectConfig] = None
    dataset: Optional[Dataset] = None
    teachable_machine_link: Optional[str] = Field(None, description="Teachable Machine model link for image recognition projects")


class TrainingConfig(BaseModel):
    epochs: Optional[int] = Field(100, ge=1, le=10000)
    batchSize: Optional[int] = Field(32, ge=1, le=10000)
    learningRate: Optional[float] = Field(0.001, gt=0, le=1)
    validationSplit: Optional[float] = Field(0.2, gt=0, lt=1)


class ExampleAdd(BaseModel):
    text: str = Field(..., description="Text example to add")
    label: str = Field(..., description="Label for this example")

class ExamplesBulkAdd(BaseModel):
    examples: List[ExampleAdd] = Field(..., description="List of examples to add")

class DatasetUpload(BaseModel):
    records: Optional[int] = Field(None, ge=0)
    description: Optional[str] = Field("")


class TrainingJob(BaseModel):
    id: str = Field(..., description="Training job identifier")
    projectId: str = Field(..., description="Project ID")
    status: str = Field("queued", description="Job status: queued|training|ready|failed")
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    startedAt: Optional[datetime] = Field(None, description="When training started")
    completedAt: Optional[datetime] = Field(None, description="When training completed")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: float = Field(0.0, ge=0.0, le=100.0, description="Training progress percentage")
    config: Optional[ProjectConfig] = Field(None, description="Training configuration")
    result: Optional[dict] = Field(None, description="Training results (accuracy, etc.)")

class TrainingJobStatus(str, Enum):
    QUEUED = "queued"
    TRAINING = "training"
    READY = "ready"
    FAILED = "failed"


class FileUploadResponse(BaseModel):
    success: bool
    gcsPath: str


class TrainingResponse(BaseModel):
    success: bool
    message: str
    jobId: Optional[str] = Field(None, description="Training job ID")

class PredictionRequest(BaseModel):
    text: str = Field(..., description="Text to predict")

class PredictionResponse(BaseModel):
    success: bool
    label: str
    confidence: float
    alternatives: List[dict] = Field(default_factory=list, description="Alternative predictions")


class ProjectStatusResponse(BaseModel):
    id: str
    status: ProjectStatus
    dataset: Dataset
    datasets: List[Dataset]
    model: TrainedModel
    updatedAt: datetime


class PaginationInfo(BaseModel):
    limit: int
    offset: int
    total: int


class ProjectListResponse(BaseModel):
    success: bool = True
    data: List[Project]
    pagination: PaginationInfo


class ProjectResponse(BaseModel):
    success: bool = True
    data: Project


class ProjectStatusResponseWrapper(BaseModel):
    success: bool = True
    data: ProjectStatusResponse


class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[List[str]] = None

# New Demo Project Models
class DemoProject(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    demo_project_id: str = Field(..., description="Unique demo project identifier")
    name: str = Field(..., description="Demo project name")
    description: str = Field(..., description="Project description")
    teacher_id: str = Field(..., description="Teacher who created this demo")
    classroom_id: str = Field(..., description="Classroom this demo belongs to")
    project_type: str = Field(..., description="Type of project (e.g., 'text_classification', 'image_classification')")
    dataset_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dataset information")
    trained_model_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Trained model information")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    active: bool = Field(True, description="Whether demo project is active")

class DemoProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Demo project name")
    description: str = Field(..., min_length=1, max_length=500, description="Project description")
    project_type: str = Field(..., description="Type of project")
    dataset_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Dataset information")
    trained_model_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Trained model information")

class DemoProjectResponse(BaseModel):
    success: bool = True
    data: DemoProject

class DemoProjectListResponse(BaseModel):
    success: bool = True
    data: List[DemoProject]

# New Guest Models
class Guest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    session_id: str = Field(..., description="Unique session ID")
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    expiresAt: datetime = Field(..., description="Session expiration timestamp")
    active: bool = Field(True, description="Whether session is active")
    
    # Optional metadata fields for tracking
    ip_address: Optional[str] = Field(None, description="IP address of the guest")
    user_agent: Optional[str] = Field(None, description="User agent string")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")
    
    # Project data stored directly in guest collection
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(..., description="Project name")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Project creation timestamp")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last update timestamp")
    status: str = Field("draft", description="Project status: draft, training, trained, failed")
    
    # Dataset information
    dataset_type: str = Field("text", description="Type of dataset (text, image, etc.)")
    dataset: List[Dict[str, str]] = Field(default_factory=list, description="Training examples with input and label")
    dataset_size: int = Field(0, description="Number of training examples")
    
    # Model information
    model_type: str = Field("logistic_regression", description="Type of model used")
    model_version: int = Field(1, description="Model version number")
    ml_config: Dict[str, Any] = Field(default_factory=dict, description="Model configuration parameters")
    
    # Training information
    training_status: str = Field("pending", description="Training status: pending, training, completed, failed")
    training_logs: List[str] = Field(default_factory=list, description="Training progress logs")
    trained_at: Optional[datetime] = Field(None, description="When training completed")
    metrics: Dict[str, float] = Field(default_factory=dict, description="Training metrics (accuracy, loss, f1)")
    currentJobId: Optional[str] = Field(None, description="Current training job ID")
    
    # Test results
    test_results: List[Dict[str, str]] = Field(default_factory=list, description="Test predictions with input, expected, and predicted")
    test_accuracy: Optional[float] = Field(None, description="Test accuracy score")
    last_tested_at: Optional[datetime] = Field(None, description="Last test timestamp")
    
    # Scratch integration
    scratch_api_key: Optional[str] = Field(None, description="Scratch API key for integration")
    scratch_enabled: bool = Field(False, description="Whether Scratch integration is enabled")
    usage_count: int = Field(0, description="Number of times project was used")
    
    # Access tracking
    last_accessed_by: Optional[str] = Field(None, description="Last user who accessed the project")
    last_accessed_at: Optional[datetime] = Field(None, description="Last access timestamp")

class GuestCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Project name")
    dataset_type: str = Field("text", description="Type of dataset")
    session_duration_hours: int = Field(48, ge=1, le=168, description="Session duration in hours (1-168 hours = 1 week max)")

class GuestUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    dataset: Optional[List[Dict[str, str]]] = None
    ml_config: Optional[Dict[str, Any]] = None
    training_status: Optional[str] = None
    status: Optional[str] = None
    currentJobId: Optional[str] = None
    metrics: Optional[Dict[str, float]] = None
    test_results: Optional[List[Dict[str, str]]] = None
    scratch_enabled: Optional[bool] = None

class GuestResponse(BaseModel):
    success: bool = True
    data: Guest

class GuestListResponse(BaseModel):
    success: bool = True
    data: List[Guest]

# Simple Guest Session (without project data)
class GuestSession(BaseModel):
    model_config = ConfigDict(protected_namespaces=())
    
    session_id: str = Field(..., description="Unique session ID")
    createdAt: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation timestamp")
    expiresAt: datetime = Field(..., description="Session expiration timestamp")
    active: bool = Field(True, description="Whether session is active")
    
    # Optional metadata fields for tracking
    ip_address: Optional[str] = Field(None, description="IP address of the guest")
    user_agent: Optional[str] = Field(None, description="User agent string")
    last_active: Optional[datetime] = Field(None, description="Last activity timestamp")

class GuestSessionResponse(BaseModel):
    success: bool = True
    data: GuestSession