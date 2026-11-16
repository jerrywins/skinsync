from fastapi import APIRouter, Depends
from pydantic import Field, model_validator
from sqlalchemy.engine import Connection

from .. import db
from ..security import CurrentUser, optional_user, rate_limit, require_user
from ..services import comparisons
from .common import Strict

router = APIRouter(tags=["comparisons"])


class ProductSpec(Strict):
    product_id: str | None = Field(None, max_length=200)
    product_version_id: str | None = Field(None, max_length=60)
    manual_ingredients: str | None = Field(None, max_length=8000)
    label: str | None = Field(None, max_length=120)

    @model_validator(mode="after")
    def _one(self):
        given = [x for x in (self.product_id, self.product_version_id, self.manual_ingredients) if x]
        if len(given) != 1:
            raise ValueError("give exactly one of product_id, product_version_id or manual_ingredients")
        return self


class CompareIn(Strict):
    a: ProductSpec
    b: ProductSpec


@router.post("/comparisons", dependencies=[Depends(rate_limit("compare", 60, 60))])
def create(body: CompareIn, user: CurrentUser | None = Depends(optional_user), conn: Connection = Depends(db.get_conn)):
    return comparisons.run(conn, body.a.model_dump(exclude_none=True), body.b.model_dump(exclude_none=True),
                           user.id if user else None)


@router.get("/comparisons/{comparison_id}")
def read(comparison_id: str, user: CurrentUser | None = Depends(optional_user), conn: Connection = Depends(db.get_conn)):
    _uuid_or_404(comparison_id)
    return comparisons.get(conn, comparison_id, user.id if user else None)


@router.post("/comparisons/{comparison_id}/save")
def save(comparison_id: str, user: CurrentUser = Depends(require_user), conn: Connection = Depends(db.get_conn)):
    _uuid_or_404(comparison_id)
    comparisons.save(conn, comparison_id, user.id)
    return {"saved": True}


def _uuid_or_404(v: str) -> None:
    import uuid

    from ..errors import not_found

    try:
        uuid.UUID(v)
    except ValueError as e:
        raise not_found("Comparison") from e
