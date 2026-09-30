import httpx
import pytest

from app.core.exceptions import AppException
from app.services.vertex_forecast import VertexEndpointBackend, VertexNotConfigured


async def _tok():
    return "tok"


def _be(handler, **kw):
    return VertexEndpointBackend("proj", "asia-south1", "123", transport=httpx.MockTransport(handler), token_provider=_tok, **kw)


@pytest.mark.asyncio
async def test_vertex_request_shape_and_parsing():
    seen = {}

    def h(req):
        seen["url"], seen["auth"], seen["body"] = str(req.url), req.headers["authorization"], req.content.decode()
        return httpx.Response(200, json={"predictions": [[1.0, 2.0, 3.0]]})

    r = await _be(h).forecast([1, 2, 3], 3)
    assert r.daily_forecast == [1.0, 2.0, 3.0] and r.model == "vertex:123"
    assert seen["url"].startswith("https://asia-south1-aiplatform.googleapis.com/v1/projects/proj/locations/asia-south1/endpoints/123:predict")
    assert seen["auth"] == "Bearer tok" and '"horizon_days":3' in seen["body"]


@pytest.mark.asyncio
@pytest.mark.parametrize("resp,code", [
    (httpx.Response(500), "VERTEX_ERROR"), (httpx.Response(429), "VERTEX_ERROR"),
    (httpx.Response(200, json={"predictions": [[1.0]]}), "VERTEX_MALFORMED"),     # wrong horizon length
    (httpx.Response(200, json={"predictions": [[-1.0, 2.0]]}), "VERTEX_MALFORMED"),  # negative demand
    (httpx.Response(200, json={"nope": 1}), "VERTEX_MALFORMED"),
])
async def test_vertex_failures_never_fabricate(resp, code):
    with pytest.raises(AppException) as e:
        await _be(lambda r: resp).forecast([1, 2], 2)
    assert e.value.error_code == code


@pytest.mark.asyncio
async def test_vertex_timeout_and_missing_credentials():
    def slow(req):
        raise httpx.ReadTimeout("t", request=req)

    with pytest.raises(AppException) as e:
        await _be(slow).forecast([1], 1)
    assert e.value.error_code == "VERTEX_TIMEOUT"

    from app.integrations.google.errors import NotConfigured

    async def no_creds():
        raise NotConfigured("Google credentials")

    be = VertexEndpointBackend("p", "l", "e", token_provider=no_creds)
    with pytest.raises(VertexNotConfigured):
        await be.forecast([1], 1)
