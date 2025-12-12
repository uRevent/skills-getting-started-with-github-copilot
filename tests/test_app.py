from src import app as app_module  # type: ignore
from fastapi.testclient import TestClient  # type: ignore
import copy
import pathlib
import sys

# Ensure project root is on sys.path
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Snapshot initial in-memory DB so we can reset between tests
_INITIAL_ACTIVITIES = copy.deepcopy(app_module.activities)


def reset_state():
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(_INITIAL_ACTIVITIES))


def get_client():
    return TestClient(app_module.app)


def test_get_activities_returns_data():
    reset_state()
    client = get_client()

    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()

    # Basic shape checks
    assert isinstance(data, dict)
    assert "Soccer Team" in data
    assert "Drama Club" in data
    assert isinstance(data["Drama Club"]["participants"], list)


def test_signup_success_and_reflected_in_list():
    reset_state()
    client = get_client()

    activity = "Science Club"
    email = "newstudent@mergington.edu"

    # Sign up
    resp = client.post(
        f"/activities/{activity}/signup", params={"email": email})
    assert resp.status_code == 200
    assert f"Signed up {email} for {activity}" in resp.json()["message"]

    # Verify in list
    resp2 = client.get("/activities")
    assert resp2.status_code == 200
    data = resp2.json()
    assert email in data[activity]["participants"]


def test_signup_duplicate_returns_400():
    reset_state()
    client = get_client()

    activity = "Drama Club"
    existing_email = "emily@mergington.edu"

    # Attempt duplicate
    resp = client.post(
        f"/activities/{activity}/signup", params={"email": existing_email})
    assert resp.status_code == 400
    assert "already signed up" in resp.json()["detail"]


def test_signup_activity_not_found_returns_404():
    reset_state()
    client = get_client()

    resp = client.post(
        "/activities/Nonexistent Activity/signup", params={"email": "x@y.z"})
    assert resp.status_code == 404


def test_unregister_success_and_removed_from_list():
    reset_state()
    client = get_client()

    activity = "Basketball Team"
    email = "sarah@mergington.edu"  # initially present

    resp = client.post(
        f"/activities/{activity}/unregister", params={"email": email})
    assert resp.status_code == 200
    assert f"Unregistered {email} from {activity}" in resp.json()["message"]

    # Verify removal
    resp2 = client.get("/activities")
    assert resp2.status_code == 200
    data = resp2.json()
    assert email not in data[activity]["participants"]


def test_unregister_not_registered_returns_404():
    reset_state()
    client = get_client()

    activity = "Science Club"
    email = "nobody@mergington.edu"  # not present

    resp = client.post(
        f"/activities/{activity}/unregister", params={"email": email})
    assert resp.status_code == 404


def test_unregister_activity_not_found_returns_404():
    reset_state()
    client = get_client()

    resp = client.post("/activities/Fake Club/unregister",
                       params={"email": "x@y.z"})
    assert resp.status_code == 404
