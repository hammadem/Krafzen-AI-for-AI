from app.services.aec_model_registry import model_registry

def test_registry_matches_real_artifacts():
    r=model_registry()
    assert r["reference_count"]==len(r["references"])>=13
    models={m["mode"]:m for m in r["models"]}
    assert models["server_advisory"]["correct"]==31
    assert models["browser_advisory"]["correct"]==206
    assert models["offline_experiment"]["runtime_available"] is False
    assert models["offline_experiment"]["correct"]==6
    assert any(s["name"]=="CubiCasa5K" and s["training_use"]=="excluded" for s in r["datasets"])
