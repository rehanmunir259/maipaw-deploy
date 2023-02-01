from fastapi.encoders import jsonable_encoder

from pydantic import BaseModel, Field
from typing import List, Optional, Union
import datetime

from .objectid import PydanticObjectId

class Quantity(BaseModel):
    quantity: Optional[Union[str, int, float]]
    unit: Optional[str]


class Ingredient(BaseModel):
    name: str
    quantity: Optional[Quantity]


class Post(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    author: str
    text: str
    tags: str


class Cocktail(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    slug: str
    name: str
    postid: PydanticObjectId
#     ingredients: List[Ingredient]
#     instructions: List[str]
#     date_added: Optional[datetime]
#     date_updated: Optional[datetime]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data



class Role(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    name: str


    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data


class User(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    email: str
    code: Optional[str]
    role: Optional[PydanticObjectId]
    is_blocked: Optional[bool]

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data

class Style(BaseModel):
# 50 unique avatars (5 variations of 10 styles) (2.29$)
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    image: str
    name: str


    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data


class Package(BaseModel):
# 50 unique avatars (5 variations of 10 styles) (2.29$)
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    avatars: int
    variations: int
    styles: int
    price: int

    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data



class Order(BaseModel):
    id: Optional[PydanticObjectId] = Field(None, alias="_id")
    user_id: Optional[PydanticObjectId]
    package: Optional[Package]
    styles: Optional[List[Style]]
    input_images: Optional[List[str]]
    output_images: Optional[List[str]] = None
    status: Optional[str]
    last_modified: Optional[datetime.datetime]

    user: Optional[List[User]]
    def to_json(self):
        return jsonable_encoder(self, exclude_none=True)

    def to_bson(self):
        data = self.dict(by_alias=True, exclude_none=True)
        if data.get("_id") is None:
            data.pop("_id", None)
        return data