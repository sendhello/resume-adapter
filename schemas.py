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


class CareerHistory(BaseModel):
    position: str
    company: str
    location: str
    dates: str
    responsibilities: List[str]


class Resume(BaseModel):
    company_name: str
    name: str
    title: str
    phone: str
    email: str
    address: str
    personal_summary: str
    skills: dict[str, List[str]]
    career_history: List[CareerHistory]
    education: List[Education]
    certificates: List[Education]
    websites: dict[str, str]
    languages: List[str]
    hobbies_interests: List[str]
    work_rights: str


class ResumeResponse(BaseModel):
    resume: Resume
    cover_letter: str
