import logging
import uuid
from typing import Annotated

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# from app.core.config import settings

logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer()


async def get_current_user_id(
    token: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> uuid.UUID:
    """
    Dependency to verify JWT token by calling auth_service and return user ID
    """
    # token = request.headers.get("Authtorization")
    # if not token or not token.startswith("Bearer "):
    #     logger.debug("Header is missing or invalid")
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Unauthtorizarted",
    #         headers={"WWW-Authenticate": "Bearer"},
    #     )
    auth_token = token.credentials
    if not auth_token: # Should not happen if HTTPBearer worked, but safe check
        logger.error("HTTPBearer dependency did not provide credentials")
        raise HTTPException(
             status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token credentials"
         )

    auth_service_url = "http://auth_service:8000/users/me"
    headers = {"Authorization": f"Bearer {auth_token}"}

    async with httpx.AsyncClient() as client:
        try:
            logger.debug(f"Calling auth service at {auth_service_url}")
            response = await client.get(auth_service_url, headers=headers)
            response.raise_for_status()  # Raise HTTPStatusError for 4xx/5xx responses

            user_data = response.json()
            user_id_str = user_data.get("id")
            if not user_id_str:
                logger.error("Auth service response missing 'id' field")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Invalid response from authentication service",
                )
            logger.debug(f"Token validated for user_id: {user_id_str}")
            return uuid.UUID(user_id_str) # Convert string UUID to UUID object
        except httpx.ConnectError:
            logger.error(f"Could not connect to auth service at {auth_service_url}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Authentication service is unavailable.",
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == status.HTTP_401_UNAUTHORIZED:
                logger.debug("Auth service returned 401, invalid token")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from e
            else:
                # Handle other errors from auth service (e.g., 500)
                logger.error(
                    f"Auth service returned error {e.response.status_code}: {e.response.text}"
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="An error occurred during authentication.",
                ) from e
        except Exception as e:
            # Catch any other unexpected errors (e.g., JSON decode error, UUID conversion)
            logger.exception(f"Unexpected error during token validation: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="An unexpected error occurred.",
            ) from e

# Type alias for dependency injection clarity
CurrentUserUUID = Annotated[uuid.UUID, Depends(get_current_user_id)]
