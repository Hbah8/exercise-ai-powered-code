import copy
import importlib.util
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


def load_app_module():
    path = Path(__file__).resolve().parents[1] / "src" / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def client():
    mod = load_app_module()
    original = copy.deepcopy(mod.activities)
    client = TestClient(mod.app)
    yield client
    # restore in-memory activities state
    mod.activities.clear()
    mod.activities.update(original)


def test_get_activities(client):
    res = client.get("/activities")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)
    assert "Basketball" in data


def test_signup_and_unregister(client):
    email = "tester@school.edu"

    # Sign up
    res = client.post("/activities/Basketball/signup", params={"email": email})
    assert res.status_code == 200

    data = client.get("/activities").json()
    assert email in data["Basketball"]["participants"]

    # Signing up again should fail
    res2 = client.post("/activities/Basketball/signup", params={"email": email})
    assert res2.status_code == 400

    # Unregister
    res3 = client.delete("/activities/Basketball/participants", params={"email": email})
    assert res3.status_code == 200

    data_after = client.get("/activities").json()
    assert email not in data_after["Basketball"]["participants"]


def test_activity_not_found(client):
    res = client.post("/activities/Nonexistent/signup", params={"email": "a@b.com"})
    assert res.status_code == 404


def test_unregister_not_found(client):
    res = client.delete("/activities/Basketball/participants", params={"email": "noone@x.com"})
    assert res.status_code == 404
