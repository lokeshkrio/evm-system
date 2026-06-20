import pytest
from pydantic import BaseModel
from server.rpc_dispatcher import RPCDispatcher
from server.protocol import RPCRequest, RPCResponse

class DummyParams(BaseModel):
    value: int

@pytest.mark.asyncio
async def test_rpc_dispatcher():
    dispatcher = RPCDispatcher()
    
    async def dummy_method(value: int):
        return {"result": value * 2}
        
    dispatcher.register("dummy", dummy_method, DummyParams)
    
    req = RPCRequest(jsonrpc="2.0", method="dummy", params={"value": 5}, id="1")
    resp = await dispatcher.dispatch(req)
    
    assert isinstance(resp, RPCResponse)
    assert resp.result == {"result": 10}
