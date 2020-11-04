
from typing import Optional, List, Union, Dict, Type
from pydantic import BaseModel, constr
from jwcrypto import jwk, jwt


import logging

# JSON Web Token
class Payload(BaseModel):
    """Represents the payload of claims in a JWT"""
    iss: str = "admin"
    sub: str = "admin base jwt"
    aud: Union[str,List[str]] = "admin"

    exp: int
    nbf: Optional[int] = 0
    iat: int

    jti: Optional[str] = ""

    def sign_serialize(self, private_key: str):
        """Serialize a JWT into it's serialized form"""

        key = jwk.JWK.from_pem(data=private_key.encode('utf-8'))

        t = jwt.JWT(
            header={"alg": "RS256"},
            claims=self.json()
        )
        t.make_signed_token(key)
        

        return Serialized(
            token=t.serialize(compact=True)
        )

class Serialized(BaseModel):
    """Holds a serialized JWT"""
    token: str
    
    def deserialize_verify(self, model: Type[Payload], public_key: str):
        """Attempt to deserialize and verify the JWT's signature. Then against the claims in a given payload model"""

        key = jwk.JWK.from_pem(data=public_key.encode("utf-8"))
        t = jwt.JWT(key=key, jwt=self.token, algs=["RS256"])

        return model.parse_raw(t.claims)

class OpenIDScope(BaseModel):
    sub: str

class ProfileScope(BaseModel):
    name: Optional[str]
    family_name: Optional[str]
    given_name: Optional[str]
    middle_name: Optional[str]
    nickname: Optional[str]
    preferred_username: Optional[str]
    profile: Optional[str]
    picture: Optional[str]
    website: Optional[str]
    gender: Optional[str]
    birthdate: Optional[str]
    zoneinfo: Optional[str]
    locale: Optional[str]
    updated_at: Optional[int]

class EmailScope(BaseModel):
    email: str
    email_verified: Optional[bool]

class OpenIDToken(OpenIDScope, Payload):
    pass

class EmailToken(EmailScope, OpenIDToken, Payload):
    pass

# # Keycloak roles
# class RolesScope(BaseModel):
#     class RealmAccess(BaseModel):
#         roles: List[str]

#     aud: Optional[str]
#     realm_access: RealmAccess
#     resource_access: Dict[str, Dict[str, List[str]]]

# class KeycloakAccessToken(Payload, OpenIDScope, ProfileScope, EmailScope, RolesScope):
#     pass