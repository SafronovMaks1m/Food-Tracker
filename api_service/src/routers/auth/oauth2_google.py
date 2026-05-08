from fastapi import APIRouter, Header, status, Query, Depends, HTTPException
import jwt
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.auth.auth import get_current_session_optional
from src.models.sessions import Sessions
from src.services.auth.session_service import SessionService
from src.database.db_depends import get_async_db
from src.models.users import Users
from src.services.auth.generate_redirect_uri_google import GenerateOauthRedirectUri
from src.services.auth.google_auth_service import GoogleAuthService
from src.dependencies.correct_user import check_user_blocked
from loguru import logger

router = APIRouter(
    prefix="/oauth2-google"
)

@router.get("/url") #когда будем делать фронт для мобилы этого метода не будет
def get_google_oauth_redirect_uri():
    uri = GenerateOauthRedirectUri.generate_google_oauth_redirect_uri()
    return uri

@router.get("/callback", status_code=status.HTTP_201_CREATED) #когда будет мобилка станет post, а также добавится code_verifier с мобилки
async def login_google_user(
    device: str = Header(default="dfsgsrdtgsdfg2132dsgfdsg4"), #пока что по дефолту, чтобы протестить
    error: str | None = Query(None),
    code: str | None  = Query(None),
    db: AsyncSession = Depends(get_async_db),
    session: Sessions = Depends(get_current_session_optional)
):
    if session is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are already logged in"
        )
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Не удалось войти через Google. Попробуйте еще раз"
        )
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Не удалось войти через Google. Попробуйте еще раз"
        )
    response = await GoogleAuthService.get_responce_google(code)
    if response["status"] != 200:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Не удалось войти через Google. Попробуйте еще раз"
        )
    content_type = response["Content-Type"]
    if "application/json" not in content_type:
        logger.error(
            f"При запросе к Google aouth пришёл не json, а {content_type}."
            f"Тело ответа (первые 100 символов): {response.text[:100]}"
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, 
            detail="Проблема на стороне сервера авторизации. Мы уже чиним"
        )
    
    id_token = response["body"]["id_token"]
    cur_user = jwt.decode(
                id_token,
                algorithms=["RS256"],
                options={"verify_signature": False}
            )
    sub, email, name, picture = [cur_user.get(i) for i in ["sub", "email", "name", "picture"]]
    db_user = await db.scalar(
        select(Users)
        .where(or_(Users.google_id == sub, Users.email == email))
    )
    
    if db_user is None:
        db_user = Users(
            name = name,
            email = email,
            google_id = sub,
            avatar_url = picture
        )
        db.add(db_user)
        await db.flush()
    else:
        check_user_blocked(db_user)
        if not db_user.google_id:
            db_user.google_id = sub
            if not db_user.avatar_url:
                db_user.avatar_url = picture
                
    session_serv = SessionService(db_user, db)
    result = await session_serv.create_or_update_session(device)
    print(result)

