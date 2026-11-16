"""Privacy-respecting funnel analytics (SkinIQ §62). Sent only after the visitor consents
(enforced client-side and by the `consent` flag). No PII and no skin data are accepted."""

from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import Field

from .. import db
from ..security import rate_limit
from .common import Strict

router = APIRouter(tags=["analytics"])

EVENT = Literal[
    "landing_view", "comparison_started", "product_search", "product_selected", "comparison_completed",
    "skin_analysis_started", "skin_image_uploaded", "skin_image_quality_failed", "skin_analysis_completed",
    "skin_observation_viewed", "skin_recommendation_clicked", "alternative_search_started",
    "alternative_product_identified", "alternative_search_completed", "alternative_clicked", "alternative_compared",
    "ingredient_viewed", "routine_created", "routine_analyzed", "product_saved", "share_created", "share_viewed",
    "signup_started", "signup_completed",
]


class EventIn(Strict):
    name: EVENT
    consent: Literal[True]
    session_id: str = Field(min_length=8, max_length=64, pattern=r"^[A-Za-z0-9-]+$")
    route: str | None = Field(None, max_length=120, pattern=r"^/[A-Za-z0-9/_\-\[\]]*$")
    metadata: dict[str, str | int | bool] = Field(default_factory=dict, max_length=8)


@router.post("/events", status_code=202, dependencies=[Depends(rate_limit("events", 300, 60))])
def track(body: EventIn, conn=Depends(db.get_conn)):
    meta = {k[:40]: (v[:80] if isinstance(v, str) else v) for k, v in body.metadata.items()}
    import json

    db.execute(conn, """INSERT INTO analytics_events (name, session_id, route, metadata)
                        VALUES (:n, :s, :r, CAST(:m AS jsonb))""", n=body.name, s=body.session_id, r=body.route,
               m=json.dumps(meta))
    return {"accepted": True}
