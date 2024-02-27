import logging
import requests
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from jose import jwt, jwk, JWTError, ExpiredSignatureError


class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, jwks_url: str):
        super().__init__(app)
        self.jwks = self.get_jwks(jwks_url)
        self.logger = logging.getLogger("AuthMiddleware")

    @staticmethod
    def get_jwks(url: str) -> dict[str, dict[str, str]]:
        response = requests.get(url).json()
        keys = response["keys"]
        return {
            key["kid"]: {"n": key["n"], "e": key["e"], "kty": key["kty"]}
            for key in keys
        }

    def decode_jwt(self, token: str):
        unverified_header = jwt.get_unverified_headers(token)
        kid = unverified_header["kid"]
        if kid not in self.jwks:
            raise HTTPException(status_code=403, detail="kid not recognized")
        try:
            public_key = jwk.construct(
                key_data=self.jwks[kid], algorithm="RS256"
            ).to_pem()
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            self.logger.info(f"Decoded JWT: {payload}")
            return payload

        except ExpiredSignatureError as e:
            raise HTTPException(status_code=403, detail="ExpiredToken")
        except JWTError as e:
            raise HTTPException(
                status_code=403, detail=f"Invalid authentication credentials: {e}"
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"An error occurred: {e}")

    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/search/faces/health_check":
            return await call_next(request)

        token: str = request.headers.get("Authorization")
        if token:
            try:
                user_info = self.decode_jwt(token=token)
                request.state.user = user_info
            except ValueError:
                raise HTTPException(
                    status_code=403, detail="Invalid authorization header"
                )
            except HTTPException as e:
                raise e
        return await call_next(request)
