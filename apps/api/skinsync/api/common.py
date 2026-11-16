from pydantic import BaseModel, ConfigDict


class Strict(BaseModel):
    """Request bodies reject unknown fields (NFR-02)."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


def page(limit: int, offset: int, total: int, items: list) -> dict:
    nxt = offset + limit if offset + limit < total else None
    return {"items": items, "total": total, "limit": limit, "offset": offset, "next_offset": nxt}
