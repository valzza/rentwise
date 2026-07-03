"""Export & import for five datasets in CSV, Excel and JSON.

Exporting uses pandas (already a dependency); Excel needs openpyxl.
Importing supports CSV and JSON for properties and users with row-level
validation so a single bad row doesn't abort the whole file.
"""
import io
import json
from typing import List, Dict, Any, Tuple

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_models import User
from app.models.domain_models import (
    Property, ViewingBooking, RentalApplication, Payment,
)
from app.core.security import hash_password

EXPORTABLE = {"properties", "users", "bookings", "applications", "payments"}
IMPORTABLE = {"properties", "users"}


# ── Row builders (explicit columns; never leak password hashes etc.) ──────
def _user_row(u: User) -> Dict[str, Any]:
    return {"id": u.id, "first_name": u.first_name, "last_name": u.last_name,
            "email": u.email, "is_active": u.is_active, "created_at": u.created_at}


def _property_row(p: Property) -> Dict[str, Any]:
    return {"id": p.id, "landlord_id": p.landlord_id, "title": p.title,
            "price": float(p.price), "city_id": p.city_id, "size_m2": float(p.size_m2),
            "num_rooms": p.num_rooms, "num_bathrooms": p.num_bathrooms,
            "status": p.status, "created_at": p.created_at}


def _booking_row(b: ViewingBooking) -> Dict[str, Any]:
    return {"id": b.id, "property_id": b.property_id, "tenant_id": b.tenant_id,
            "scheduled_at": b.scheduled_at, "status": b.status, "created_at": b.created_at}


def _application_row(a: RentalApplication) -> Dict[str, Any]:
    return {"id": a.id, "property_id": a.property_id, "tenant_id": a.tenant_id,
            "status": a.status, "message": a.message, "created_at": a.created_at}


def _payment_row(p: Payment) -> Dict[str, Any]:
    return {"id": p.id, "lease_id": p.lease_id, "tenant_id": p.tenant_id,
            "amount": float(p.amount), "type": p.type, "status": p.status,
            "created_at": p.created_at}


_MODELS = {
    "properties": (Property, _property_row),
    "users": (User, _user_row),
    "bookings": (ViewingBooking, _booking_row),
    "applications": (RentalApplication, _application_row),
    "payments": (Payment, _payment_row),
}


class ExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _rows(self, entity: str) -> List[Dict[str, Any]]:
        model, builder = _MODELS[entity]
        result = await self.db.execute(select(model))
        return [builder(r) for r in result.scalars().all()]

    async def export(self, entity: str, fmt: str) -> Tuple[bytes, str, str]:
        """Returns (content_bytes, media_type, filename)."""
        if entity not in EXPORTABLE:
            raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Unknown entity '{entity}'")

        rows = await self._rows(entity)
        df = pd.DataFrame(rows)

        if fmt == "csv":
            return df.to_csv(index=False).encode(), "text/csv", f"{entity}.csv"
        if fmt == "json":
            return (df.to_json(orient="records", date_format="iso", indent=2).encode(),
                    "application/json", f"{entity}.json")
        if fmt in ("xlsx", "excel"):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name=entity)
            return (buf.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    f"{entity}.xlsx")

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="format must be csv, xlsx or json")

    async def import_rows(self, entity: str, raw: bytes, content_type: str) -> Dict[str, Any]:
        if entity not in IMPORTABLE:
            raise HTTPException(status.HTTP_400_BAD_REQUEST,
                                detail=f"Import not supported for '{entity}'. Allowed: {sorted(IMPORTABLE)}")

        # Parse to a list of dict rows
        try:
            if "json" in content_type or raw.strip().startswith(b"["):
                records = json.loads(raw.decode())
            else:
                records = pd.read_csv(io.BytesIO(raw)).to_dict(orient="records")
        except Exception as e:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=f"Could not parse file: {e}")

        inserted, errors = 0, []
        for i, row in enumerate(records, start=1):
            try:
                if entity == "users":
                    await self._import_user(row)
                else:
                    await self._import_property(row)
                inserted += 1
            except Exception as e:
                errors.append({"row": i, "error": str(e)})

        await self.db.commit()
        return {"inserted": inserted, "failed": len(errors), "errors": errors}

    async def _import_user(self, row: dict) -> None:
        for field in ("first_name", "last_name", "email"):
            if not row.get(field):
                raise ValueError(f"Missing required field '{field}'")
        self.db.add(User(
            first_name=str(row["first_name"]),
            last_name=str(row["last_name"]),
            email=str(row["email"]),
            password_hash=hash_password(str(row.get("password", "ChangeMe123"))),
            is_active=bool(row.get("is_active", True)),
        ))

    async def _import_property(self, row: dict) -> None:
        for field in ("landlord_id", "title", "price", "city_id", "size_m2", "num_rooms", "num_bathrooms"):
            if row.get(field) in (None, ""):
                raise ValueError(f"Missing required field '{field}'")
        self.db.add(Property(
            landlord_id=int(row["landlord_id"]),
            title=str(row["title"]),
            description=row.get("description"),
            price=float(row["price"]),
            city_id=int(row["city_id"]),
            size_m2=float(row["size_m2"]),
            num_rooms=int(row["num_rooms"]),
            num_bathrooms=int(row["num_bathrooms"]),
            status=str(row.get("status", "active")),
        ))
