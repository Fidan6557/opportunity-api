import json
import uuid
from datetime import date
from pathlib import Path
from typing import Any, List, Optional, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, HttpUrl, ValidationError

app = FastAPI(title="Opportunity Tracker API")

DB_FILE = Path(__file__).with_name("opportunities.txt")

CategoryType = Literal[
    "internship",
    "scholarship",
    "bootcamp",
    "hackathon",
    "event",
    "fellowship",
    "volunteer",
    "competition",
]

StatusType = Literal["open", "closed", "upcoming", "expired"]


class OpportunityBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=120)
    organization: str = Field(..., min_length=2, max_length=100)
    category: CategoryType
    location: str = Field(..., min_length=2, max_length=100)
    deadline: date
    description: str = Field(..., min_length=10, max_length=500)
    source_url: HttpUrl
    is_remote: bool = False
    application_fee: float = Field(0, ge=0)
    tags: List[str] = Field(default_factory=list)
    status: StatusType = "open"


class OpportunityCreate(OpportunityBase):
    pass


class OpportunityUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=120)
    organization: Optional[str] = Field(None, min_length=2, max_length=100)
    category: Optional[CategoryType] = None
    location: Optional[str] = Field(None, min_length=2, max_length=100)
    deadline: Optional[date] = None
    description: Optional[str] = Field(None, min_length=10, max_length=500)
    source_url: Optional[HttpUrl] = None
    is_remote: Optional[bool] = None
    application_fee: Optional[float] = Field(None, ge=0)
    tags: Optional[List[str]] = None
    status: Optional[StatusType] = None


class Opportunity(OpportunityBase):
    id: str


SAMPLE_OPPORTUNITIES = [
    {
        "id": str(uuid.uuid4()),
        "title": "Google Summer Internship 2026",
        "organization": "Google",
        "category": "internship",
        "location": "London, UK",
        "deadline": "2026-05-20",
        "description": "Software engineering internship for undergraduate students interested in large-scale products and AI systems.",
        "source_url": "https://careers.google.com/",
        "is_remote": False,
        "application_fee": 0,
        "tags": ["software", "students", "summer", "ai"],
        "status": "open",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "AI Skills Bootcamp 2026",
        "organization": "Miuul",
        "category": "bootcamp",
        "location": "Online",
        "deadline": "2026-06-10",
        "description": "An intensive bootcamp covering Python, machine learning, model evaluation, and project-based learning.",
        "source_url": "https://www.miuul.com/",
        "is_remote": True,
        "application_fee": 0,
        "tags": ["python", "machine-learning", "bootcamp"],
        "status": "open",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Women in Tech Scholarship Program",
        "organization": "TechForFuture",
        "category": "scholarship",
        "location": "Baku, Azerbaijan",
        "deadline": "2026-07-01",
        "description": "Scholarship opportunity for female students pursuing technology and innovation related fields.",
        "source_url": "https://example.org/women-in-tech-scholarship",
        "is_remote": False,
        "application_fee": 0,
        "tags": ["women", "technology", "scholarship", "students"],
        "status": "upcoming",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "Baku Innovation Hackathon",
        "organization": "Baku Innovation Center",
        "category": "hackathon",
        "location": "Baku, Azerbaijan",
        "deadline": "2026-05-05",
        "description": "48-hour hackathon focused on smart city, fintech, and AI-driven startup ideas.",
        "source_url": "https://example.org/baku-hackathon",
        "is_remote": False,
        "application_fee": 15,
        "tags": ["hackathon", "startup", "ai", "smart-city"],
        "status": "open",
    },
    {
        "id": str(uuid.uuid4()),
        "title": "UN Youth Volunteer Program",
        "organization": "United Nations Youth",
        "category": "volunteer",
        "location": "Online",
        "deadline": "2026-08-15",
        "description": "Volunteer opportunity for young people to support education, outreach, and digital community projects.",
        "source_url": "https://example.org/un-youth-volunteer",
        "is_remote": True,
        "application_fee": 0,
        "tags": ["volunteer", "youth", "community", "online"],
        "status": "open",
    },
]


def initialize_db() -> None:
    if not DB_FILE.exists() or not DB_FILE.read_text(encoding="utf-8").strip():
        DB_FILE.write_text(
            "\n".join(json.dumps(item) for item in SAMPLE_OPPORTUNITIES),
            encoding="utf-8",
        )


def normalize_opportunity_data(item: dict[str, Any]) -> dict[str, Any]:
    normalized = item.copy()

    legacy_field_names = {
        "organizer": "organization",
        "is_online": "is_remote",
        "fee": "application_fee",
        "link": "source_url",
    }
    for old_name, new_name in legacy_field_names.items():
        if new_name not in normalized and old_name in normalized:
            normalized[new_name] = normalized[old_name]

    normalized.setdefault("description", f"Opportunity from {normalized.get('organization', 'the listed organization')}.")
    normalized.setdefault("tags", [])

    return normalized


def read_opportunities() -> List[Opportunity]:
    initialize_db()
    data = DB_FILE.read_text(encoding="utf-8").strip()
    if not data:
        return []

    opportunities = []
    for line_number, line in enumerate(data.splitlines(), start=1):
        try:
            opportunities.append(Opportunity(**normalize_opportunity_data(json.loads(line))))
        except (json.JSONDecodeError, ValidationError) as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Invalid opportunity data on line {line_number}: {exc}",
            ) from exc

    return opportunities


def write_opportunities(opportunities: List[Opportunity]) -> None:
    DB_FILE.write_text(
        "\n".join(json.dumps(item.model_dump(mode="json")) for item in opportunities),
        encoding="utf-8",
    )


def find_opportunity_by_id(opportunity_id: str, opportunities: List[Opportunity]) -> Opportunity:
    for opportunity in opportunities:
        if opportunity.id == opportunity_id:
            return opportunity
    raise HTTPException(status_code=404, detail="Opportunity not found")


@app.get("/")
def home():
    return {
        "message": "Welcome to Opportunity Tracker API",
        "endpoints": [
            "/opportunities",
            "/opportunities/{opportunity_id}",
            "/stats",
        ],
    }


@app.get("/opportunities", response_model=List[Opportunity])
def list_opportunities(
    category: Optional[CategoryType] = None,
    status: Optional[StatusType] = None,
    organization: Optional[str] = None,
    location: Optional[str] = None,
    is_remote: Optional[bool] = None,
    tag: Optional[str] = None,
    max_fee: Optional[float] = Query(None, ge=0),
):
    opportunities = read_opportunities()

    if category:
        opportunities = [item for item in opportunities if item.category == category]
    if status:
        opportunities = [item for item in opportunities if item.status == status]
    if organization:
        opportunities = [
            item for item in opportunities
            if organization.lower() in item.organization.lower()
        ]
    if location:
        opportunities = [
            item for item in opportunities
            if location.lower() in item.location.lower()
        ]
    if is_remote is not None:
        opportunities = [item for item in opportunities if item.is_remote == is_remote]
    if tag:
        opportunities = [
            item for item in opportunities
            if tag.lower() in [existing_tag.lower() for existing_tag in item.tags]
        ]
    if max_fee is not None:
        opportunities = [item for item in opportunities if item.application_fee <= max_fee]

    return opportunities


@app.get("/opportunities/{opportunity_id}", response_model=Opportunity)
def get_opportunity(opportunity_id: str):
    opportunities = read_opportunities()
    return find_opportunity_by_id(opportunity_id, opportunities)


@app.post("/opportunities", response_model=Opportunity, status_code=201)
def create_opportunity(payload: OpportunityCreate):
    opportunities = read_opportunities()

    duplicate_exists = any(
        item.title.lower() == payload.title.lower()
        and item.organization.lower() == payload.organization.lower()
        for item in opportunities
    )
    if duplicate_exists:
        raise HTTPException(
            status_code=409,
            detail="This opportunity already exists for the same organization",
        )

    new_opportunity = Opportunity(id=str(uuid.uuid4()), **payload.model_dump())
    opportunities.append(new_opportunity)
    write_opportunities(opportunities)
    return new_opportunity


@app.put("/opportunities/{opportunity_id}", response_model=Opportunity)
def update_opportunity(opportunity_id: str, payload: OpportunityUpdate):
    opportunities = read_opportunities()

    for index, item in enumerate(opportunities):
        if item.id == opportunity_id:
            updated_opportunity = item.model_copy(
                update=payload.model_dump(exclude_none=True)
            )
            opportunities[index] = updated_opportunity
            write_opportunities(opportunities)
            return updated_opportunity

    raise HTTPException(status_code=404, detail="Opportunity not found")


@app.delete("/opportunities/{opportunity_id}")
def delete_opportunity(opportunity_id: str):
    opportunities = read_opportunities()
    filtered_opportunities = [item for item in opportunities if item.id != opportunity_id]

    if len(filtered_opportunities) == len(opportunities):
        raise HTTPException(status_code=404, detail="Opportunity not found")

    write_opportunities(filtered_opportunities)
    return {"message": "Opportunity deleted successfully"}


@app.get("/stats")
def get_stats():
    opportunities = read_opportunities()

    category_counts = {}
    for item in opportunities:
        category_counts[item.category] = category_counts.get(item.category, 0) + 1

    return {
        "total_opportunities": len(opportunities),
        "open_opportunities": len([item for item in opportunities if item.status == "open"]),
        "remote_opportunities": len([item for item in opportunities if item.is_remote]),
        "free_opportunities": len([item for item in opportunities if item.application_fee == 0]),
        "categories": category_counts,
    }
