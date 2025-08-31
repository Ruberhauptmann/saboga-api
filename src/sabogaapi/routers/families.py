"""Routes for viewing the families data."""

import math

from fastapi import APIRouter, HTTPException, Request, Response

from sabogaapi.logger import configure_logger
from sabogaapi.schemas import Family, FamilyWithBoardgames
from sabogaapi.services import FamilyService

logger = configure_logger()

router = APIRouter(
    prefix="/families",
    tags=["Families"],
    responses={404: {"description": "Not found"}},
)


def make_link(request: Request, page: int, per_page: int, rel: str) -> str:
    url = request.url_for("read_all_families").include_query_params(
        page=page, per_page=per_page
    )
    return f'<{url}>; rel="{rel}"'


@router.get("")
async def read_all_families(
    response: Response,
    request: Request,
    page: int = 1,
    per_page: int = 50,
) -> list[Family]:
    if page < 1:
        logger.warning(
            "Invalid page number",
            extra={
                "page": page,
            },
        )
        raise HTTPException(
            status_code=422,
            detail="Page number must be greater than 1",
        )

    total_count = await FamilyService.get_total_count()
    last_page = math.ceil(total_count / per_page)

    links = []
    if page > 1:
        links.append(make_link(request, page - 1, per_page, "prev"))
    if page < last_page:
        links.append(make_link(request, page + 1, per_page, "next"))
    links.extend(
        [
            make_link(request, last_page, per_page, "last"),
            make_link(request, 1, per_page, "first"),
        ]
    )
    response.headers["link"] = ", ".join(links)

    return await FamilyService.read_all_families(page=page, per_page=per_page)


@router.get("/{bgg_id}")
async def read_family(bgg_id: int) -> FamilyWithBoardgames:
    family = await FamilyService.read_family(bgg_id=bgg_id)
    if not family:
        raise HTTPException(status_code=404, detail="Family not found")
    return family
