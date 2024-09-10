# app/utils/json_encoder.py

from langchain_core.pydantic_v1 import BaseModel
from flask.json.provider import JSONProvider
import json

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, BaseModel):
            return obj.dict()
        return super().default(obj)

class CustomJSONProvider(JSONProvider):
    def dumps(self, obj, **kwargs):
        return json.dumps(obj, cls=CustomJSONEncoder, **kwargs)

    def loads(self, s, **kwargs):
        return json.loads(s, **kwargs)

