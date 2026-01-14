from enum import StrEnum

from pydantic import BaseModel
from typing import List, Dict


class ResumeType(StrEnum):
    SoftwareEngineer = "software_engineer"
    SistemAdministrator = "sistem_administrator"
    RemoteSoftwareEngineer = "remote_software_engineer"


class Education(BaseModel):
    institution: str
    location: str
    dates: str
    qualification: str


class Experience(BaseModel):
    position: str
    company: str
    location: str
    dates: str
    achievements: list[str]


class Resume(BaseModel):
    company_name: str
    name: str
    title: str
    phone: str
    email: str
    linkedin: str
    github: str
    address: str
    professional_summary: str
    key_skills: dict[str, list[str]]
    work_experience: list[Experience]
    education: list[Education]
    other_educations: list[Education]
    languages: list[str]
    hobbies: list[str]
    work_rights: str
