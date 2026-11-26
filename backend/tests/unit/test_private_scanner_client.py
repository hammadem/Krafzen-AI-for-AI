import pytest
from fastapi import HTTPException
from app.services import private_scanner_client as client

def test_disabled_by_default(monkeypatch):
    for key in ("PRIVATE_SCANNER_URL","PRIVATE_SCANNER_TOKEN","PRIVATE_SCANNER_US_PROCESSING_APPROVED"):
        monkeypatch.delenv(key,raising=False)
    assert not client.remote_requested()
    with pytest.raises(HTTPException) as err: client._config()
    assert err.value.status_code==503

@pytest.mark.parametrize("url",["http://scanner.example.com","https://user:secret@scanner.example.com","https://scanner.example.com/path","https://scanner.example.com?x=1"])
def test_invalid_transport(monkeypatch,url):
    monkeypatch.setenv("PRIVATE_SCANNER_URL",url)
    monkeypatch.setenv("PRIVATE_SCANNER_TOKEN","x"*40)
    monkeypatch.setenv("PRIVATE_SCANNER_US_PROCESSING_APPROVED","true")
    assert client.remote_requested()
    with pytest.raises(HTTPException): client._config()

def test_explicit_approval_required(monkeypatch):
    monkeypatch.setenv("PRIVATE_SCANNER_URL","https://scanner.example.com")
    monkeypatch.setenv("PRIVATE_SCANNER_TOKEN","x"*40)
    monkeypatch.delenv("PRIVATE_SCANNER_US_PROCESSING_APPROVED",raising=False)
    with pytest.raises(HTTPException): client._config()
    monkeypatch.setenv("PRIVATE_SCANNER_US_PROCESSING_APPROVED","true")
    assert client._config()[0]=="https://scanner.example.com"
