from fastapi import HTTPException, Request, status
from fastapi.staticfiles import StaticFiles

from app import crud
from app.api.deps import decode_jwt
from app.db.session import SessionLocal


async def verify_static_file_access(request: Request) -> None:
    """
    Verify client requesting a static file has access to the project associated
    with the file.

    Args:
        request (Request): Client request for a static file

    Raises:
        HTTPException: Client not authenticated
        HTTPException: User associated with access token not found
        HTTPException: User does not have access to project
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    token_data = decode_jwt(access_token.split(" ")[1])
    user = crud.user.get(SessionLocal(), id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="user not found"
        )
    project_id = request.url.path.split("/static/")[1].split("/")[0]
    project = crud.project.get_user_project(
        SessionLocal(), user_id=user.id, project_id=project_id
    )
    if not project:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)


class ProtectedStaticFiles(StaticFiles):
    """Extend StatcFiles to include user access authorization."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        assert scope["type"] == "http"

        request = Request(scope, receive)
        await verify_static_file_access(request)
        await super().__call__(scope, receive, send)