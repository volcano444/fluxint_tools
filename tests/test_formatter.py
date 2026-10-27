import json
from fluxx_api.formatter import save_json


def test_save_json_writes_pretty_json(tmp_path, monkeypatch):
    import fluxx_api.formatter as formatter
    monkeypatch.setattr(formatter, "__file__", str(tmp_path / "fluxx_api" / "formatter.py"))
    result = {"ok": True, "data": {"city": "Surabaya"}}
    path = save_json(result, "test")
    content = path.read_text(encoding="utf-8")
    assert "\n" in content
    assert json.loads(content) == result
