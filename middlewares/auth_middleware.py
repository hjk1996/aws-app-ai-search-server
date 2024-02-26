import os
import requests
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from jose import jwt, jwk


class AuthMiddleware(BaseHTTPMiddleware):

    def __init__(self, app: ASGIApp, jwks_url: str):
        super().__init__(app)
        self.jwks= self.get_jwks(jwks_url)


    @staticmethod
    def get_jwks(url: str) -> dict[str, str]:
        response = requests.get(url).json()
        keys = response["keys"]
        return {key["kid"]: key["n"] for key in keys}

    def decode_jwt(self, token: str):
        unverified_header = jwt.get_unverified_headers(token)
        kid = unverified_header["kid"]
        if kid not in self.jwks:
            raise HTTPException(status_code=403, detail="kid not recognized")
        n = self.jwks[kid]
        public_key = jwk.construct(key_data=n, algorithm="RS256").to_pem()
        try:
            payload = jwt.decode(token, public_key, algorithms=["RS256"])
            return payload
        except:
            raise HTTPException(
                status_code=403, detail="Invalid authentication credentials"
            )
    
    async def dispatch(self, request: Request, call_next):
        if request.url.path == "/search/faces/health_check":
            return await call_next(request)
        
        
        token: str = request.headers.get("Authorization")
        if token:
            try:
                user_info = self.decode_jwt(token=token)
                request.state.user = user_info
            except ValueError:
                raise HTTPException(status_code=403, detail="Invalid authorization header")
            except HTTPException as e:
                raise e
        return await call_next(request)
