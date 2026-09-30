"""Tools that every assistant may be given. They read only what the signed-in user's permissions already allow."""
from typing import Any, Dict, FrozenSet

from app.ai.base import ToolContext, ToolSpec, obj
from app.services.platform_service import NAV_CATALOGUE


def _navigation(sections: FrozenSet[str]):
  async def handler(ctx: ToolContext, args: Dict[str, Any]) -> Dict[str, Any]:
    """The real menu for this user, limited to the assistant's own sections and the user's permissions."""
    items = [
        {"screen": item["key"].split(".", 1)[1].replace("_", " ").title(), "path": item["path"], "section": item["section"]}
        for item in NAV_CATALOGUE if item["section"] in sections and ctx.user.has_permission(item["permission"])
    ]
    return {"screens_available_to_this_user": items,
            "note": "Only these screens exist for this user. Do not mention any other screen, button or link."}
  return handler


def navigation_tool(sections: FrozenSet[str]) -> ToolSpec:
    return ToolSpec(
        name="get_app_navigation",
        description="List the Med2Us screens (name and path) this user can open. Use it before telling the user where to "
                    "find something in the app, so you only name screens that really exist.",
        parameters=obj(),
        handler=_navigation(sections),
        source="Med2Us navigation menu",
    )
