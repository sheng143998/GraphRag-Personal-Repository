from enum import StrEnum


class DocumentType(StrEnum):
    TECH_NOTE = "tech_note"
    DEVELOPMENT_EXPERIENCE = "development_experience"
    PROJECT_EXPERIENCE = "project_experience"
    INTERVIEW_EXPERIENCE = "interview_experience"
    CODE_SNIPPET = "code_snippet"
    COURSE_NOTE = "course_note"
    JOB_DESCRIPTION = "job_description"


class FileType(StrEnum):
    MARKDOWN = "md"
    TEXT = "txt"
    HTML = "html"
    DOCX = "docx"
    PDF = "pdf"
    XLSX = "xlsx"
    XLS = "xls"
    CSV = "csv"
