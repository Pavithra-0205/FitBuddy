def sample_user():
    return {"name":"Test User","user_id":"TEST001","age":20,"weight":65,"goal":"muscle gain","intensity":"medium","experience_level":"beginner","days_per_week":3}

def test_homepage(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "FitBuddy" in response.text

def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_api_generation_fallback(client):
    response = client.post("/api/generate-workout", json=sample_user())
    assert response.status_code == 200
    data = response.json()
    assert len(data["plan"]["days"]) == 7
    assert data["user"]["user_id"] == "TEST001"

def test_api_feedback(client):
    client.post("/api/generate-workout", json=sample_user())
    response = client.post("/api/submit-feedback", json={"user_id":"TEST001","feedback":"Add more cardio and an extra recovery day."})
    assert response.status_code == 200
    assert len(response.json()["updated_plan"]["days"]) == 7

def test_admin_page(client):
    client.post("/api/generate-workout", json=sample_user())
    response = client.get("/view-all-users")
    assert response.status_code == 200
    assert "TEST001" in response.text
