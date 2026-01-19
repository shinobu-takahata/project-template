def test_create_example(client):
    response = client.post(
        "/api/v1/examples/", json={"name": "Test Example", "description": "Test Description"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Example"
    assert data["description"] == "Test Description"
    assert "id" in data


def test_get_example(client):
    # 作成
    create_response = client.post("/api/v1/examples/", json={"name": "Test Example"})
    example_id = create_response.json()["id"]

    # 取得
    response = client.get(f"/api/v1/examples/{example_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test Example"


def test_list_examples(client):
    # 複数作成
    client.post("/api/v1/examples/", json={"name": "Example 1"})
    client.post("/api/v1/examples/", json={"name": "Example 2"})

    # 一覧取得
    response = client.get("/api/v1/examples/")
    assert response.status_code == 200
    assert len(response.json()) == 2
