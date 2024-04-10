from fastapi import FastAPI
from starlette.responses import FileResponse
from fastapi import Request

import json
import typing

from starlette.responses import Response

from . import fetch_parking_spaces, cache_timestamp


class PrettyJSONResponse(Response):
    media_type = "application/json"

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(content, indent=2).encode("utf-8")


app = FastAPI()


@app.get("/api", response_class=PrettyJSONResponse)
def get_json_api():
    spaces = fetch_parking_spaces(end=10)
    return {
        "timestamp": cache_timestamp(),
        "spaces": spaces,
    }


@app.get("/")
def get_html():
    return FileResponse("src/index.html")
