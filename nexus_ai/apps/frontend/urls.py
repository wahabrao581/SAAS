from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse


router = APIRouter(prefix="/frontend", tags=["Frontend"])
static_dir = Path(__file__).resolve().parent / "static"


@router.get("/", include_in_schema=False)
async def frontend_home():
    return FileResponse(static_dir / "index.html")


@router.get("/subscription", include_in_schema=False)
async def subscription_page():
    return FileResponse(static_dir / "subscription.html")


@router.get("/history", include_in_schema=False)
async def history_page():
    return FileResponse(static_dir / "history.html")


@router.get("/samples", include_in_schema=False)
async def samples_page():
    return FileResponse(static_dir / "samples.html")


@router.get("/static/{asset_name}", include_in_schema=False)
async def frontend_asset(asset_name: str):
    assets = {
        "app.js": ("app.js", "text/javascript"),
        "styles.css": ("styles.css", "text/css"),
        "pages.js": ("pages.js", "text/javascript"),
        "admin-guide.md": ("admin-guide.md", "text/markdown"),
        "example.txt": ("example.txt", "text/plain"),
    }
    asset = assets.get(asset_name)
    if asset is None:
        raise HTTPException(status_code=404, detail="Frontend asset not found.")
    filename, media_type = asset
    return FileResponse(static_dir / filename, media_type=media_type)
