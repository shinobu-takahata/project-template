class TestProductsEndpoint:
    def test_register_product_returns_201(self, client):
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "ワイヤレスマウス",
                "sku": "WM-001",
                "price": 3000,
                "category": "PC周辺機器",
                "description": "Bluetooth対応",
                "initial_stock": 100,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "ワイヤレスマウス"
        assert data["sku"] == "WM-001"
        assert data["price"] == 3000
        assert data["stock_quantity"] == 100

    def test_register_product_duplicate_sku_returns_409(self, client):
        client.post(
            "/api/v1/products/",
            json={
                "name": "Product 1",
                "sku": "DUP-001",
                "price": 1000,
                "category": "Test",
                "initial_stock": 10,
            },
        )

        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Product 2",
                "sku": "DUP-001",
                "price": 2000,
                "category": "Test",
                "initial_stock": 20,
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_list_products(self, client):
        client.post(
            "/api/v1/products/",
            json={
                "name": "Product 1",
                "sku": "LIST-001",
                "price": 1000,
                "category": "Test",
                "initial_stock": 10,
            },
        )

        response = client.get("/api/v1/products/")

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) >= 1
        assert "pagination" in data

    def test_list_products_with_category_filter(self, client):
        client.post(
            "/api/v1/products/",
            json={
                "name": "Mouse",
                "sku": "CAT-001",
                "price": 1000,
                "category": "PC周辺機器",
                "initial_stock": 10,
            },
        )
        client.post(
            "/api/v1/products/",
            json={
                "name": "Desk",
                "sku": "CAT-002",
                "price": 5000,
                "category": "家具",
                "initial_stock": 5,
            },
        )

        response = client.get("/api/v1/products/?category=PC周辺機器")

        assert response.status_code == 200
        data = response.json()
        for item in data["data"]:
            assert item["category"] == "PC周辺機器"

    def test_update_product(self, client):
        create_response = client.post(
            "/api/v1/products/",
            json={
                "name": "Original",
                "sku": "UPD-001",
                "price": 1000,
                "category": "Test",
                "initial_stock": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = client.put(
            f"/api/v1/products/{product_id}",
            json={
                "name": "Updated",
                "price": 2000,
                "category": "Updated",
                "description": "New description",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated"
        assert data["price"] == 2000

    def test_update_nonexistent_product_returns_404(self, client):
        response = client.put(
            "/api/v1/products/nonexistent-id",
            json={
                "name": "Updated",
                "price": 2000,
                "category": "Test",
            },
        )

        assert response.status_code == 404

    def test_delete_product(self, client):
        create_response = client.post(
            "/api/v1/products/",
            json={
                "name": "To Delete",
                "sku": "DEL-001",
                "price": 1000,
                "category": "Test",
                "initial_stock": 10,
            },
        )
        product_id = create_response.json()["id"]

        response = client.delete(f"/api/v1/products/{product_id}")
        assert response.status_code == 204

        # 削除後は取得できない（一覧に出ない）
        list_response = client.get("/api/v1/products/")
        product_ids = [p["id"] for p in list_response.json()["data"]]
        assert product_id not in product_ids

    def test_delete_nonexistent_product_returns_404(self, client):
        response = client.delete("/api/v1/products/nonexistent-id")
        assert response.status_code == 404

    def test_register_product_invalid_price_returns_422(self, client):
        response = client.post(
            "/api/v1/products/",
            json={
                "name": "Test",
                "sku": "INV-001",
                "price": -100,
                "category": "Test",
                "initial_stock": 10,
            },
        )

        assert response.status_code == 422
