import re
from typing import Optional
from sqlalchemy.orm import Session
from app.models.tenant import Tenant


def get_tenant(db: Session, tenant_id: int) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_tenant_by_slug(db: Session, slug: str) -> Optional[Tenant]:
    return db.query(Tenant).filter(Tenant.slug == slug).first()


def create_tenant(db: Session, name: str, plan: str = "starter") -> Tenant:
    slug_candidate = re.sub(r"[^a-zA-Z0-9]+", "-", name.lower()).strip("-")
    if not slug_candidate:
        slug_candidate = "company"
    
    slug = slug_candidate
    counter = 1
    while get_tenant_by_slug(db, slug):
        slug = f"{slug_candidate}-{counter}"
        counter += 1

    tenant = Tenant(name=name, slug=slug, plan=plan)
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant
