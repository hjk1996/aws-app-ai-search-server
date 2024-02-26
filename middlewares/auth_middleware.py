import os
import requests
from fastapi import Request, HTTPException
from jose import jwt, jwk


def get_jwks(url: str) -> dict:
    response = requests.get(url).json()
    keys = response["keys"]
    return {key["kid"]: key for key in keys}


JWKS_URL = os.environ["JWKS_URL"]
jwks = get_jwks(JWKS_URL)


def decode_jwt(token: str):
    unverified_header = jwt.get_unverified_headers(token)
    kid = unverified_header["kid"]
    if kid not in jwks:
        raise HTTPException(status_code=403, detail="kid not recognized")
    jwk_data = jwks[kid]
    public_key = jwk.construct(jwk_data).to_pem()
    try:
        payload = jwt.decode(token, public_key, algorithms=["RS256"])
        return payload
    except:
        raise HTTPException(
            status_code=403, detail="Invalid authentication credentials"
        )


async def jwt_middleware(request: Request, call_next):
    authorization: str = request.headers.get("Authorization")
    if authorization:
        try:
            token = authorization.split()
            user_info = decode_jwt(token=token)
            request.state.user = user_info
        except ValueError:
            raise HTTPException(status_code=403, detail="Invalid authorization header")
        except HTTPException as e:
            return e
    return await call_next(request)
