from enum import Enum


class CategoryType(Enum):
    PROJECT = "project"
    FEATURE = "feature"
    FUNCTION = "function"
    MODULE = "module"


class NoteType(Enum):
    GENERAL = "general"
    TASK = "task"
    OPTIMIZATION = "optimization"
    BUG = "bug"
    OMIT = "omit"
    COMPLEXITY_REFINEMENT = "complexity_refinement"
    SUGGESTION = "suggestion"
    ANALYSIS = "analysis"


class DeveloperRole(Enum):
    FRONTEND_DEVELOPER = "Frontend Developer"
    BACKEND_DEVELOPER = "Backend Developer"
    FULLSTACK_DEVELOPER = "Fullstack Developer"
    DEVOPS_ENGINEER = "DevOps Engineer"
    QA_ENGINEER = "QA Engineer"
    DATA_SCIENTIST = "Data Scientist"
    MACHINE_LEARNING_ENGINEER = "Machine Learning Engineer"
    MOBILE_DEVELOPER = "Mobile Developer"
    SECURITY_ENGINEER = "Security Engineer"
    DATABASE_ADMINISTRATOR = "Database Administrator"
    SOFTWARE_ENGINEER = "Software Engineer"
    WEB_DEVELOPER = "Web Developer"
    GAME_DEVELOPER = "Game Developer"
    EMBEDDED_SYSTEMS_ENGINEER = "Embedded Systems Engineer"
    CLOUD_ENGINEER = "Cloud Engineer"


class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ON_HOLD = "on_hold"
    CANCELLED = "cancelled"


class TaskSourceType(Enum):
    NOTE = "note"
    MEETING = "meeting"
 