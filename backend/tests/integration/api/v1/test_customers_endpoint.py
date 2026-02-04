class TestCustomersEndpoint:
    def _register_customer(self, client, email="tanaka@example.com"):
        return client.post(
            "/api/v1/customers/",
            json={
                "name": "田中太郎",
                "email": email,
                "shipping_address": {
                    "label": "自宅",
                    "postal_code": "100-0001",
                    "prefecture": "東京都",
                    "city": "千代田区",
                    "street": "千代田1-1-1",
                },
            },
        )

    def test_register_customer_returns_201(self, client):
        response = self._register_customer(client)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "田中太郎"
        assert data["email"] == "tanaka@example.com"
        assert data["member_rank"] == "BRONZE"
        assert len(data["shipping_addresses"]) == 1
        assert data["shipping_addresses"][0]["is_default"] is True

    def test_register_customer_duplicate_email_returns_409(self, client):
        self._register_customer(client, email="dup@example.com")

        response = self._register_customer(client, email="dup@example.com")

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_get_customer(self, client):
        create_response = self._register_customer(
            client, email="get@example.com"
        )
        customer_id = create_response.json()["customer_id"]

        response = client.get(f"/api/v1/customers/{customer_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["customer_id"] == customer_id
        assert data["name"] == "田中太郎"
        assert len(data["shipping_addresses"]) == 1

    def test_get_nonexistent_customer_returns_404(self, client):
        response = client.get("/api/v1/customers/nonexistent-id")

        assert response.status_code == 404

    def test_update_customer(self, client):
        create_response = self._register_customer(
            client, email="update@example.com"
        )
        customer_id = create_response.json()["customer_id"]

        response = client.put(
            f"/api/v1/customers/{customer_id}",
            json={
                "name": "佐藤花子",
                "email": "sato@example.com",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "佐藤花子"
        assert data["email"] == "sato@example.com"

    def test_update_nonexistent_customer_returns_404(self, client):
        response = client.put(
            "/api/v1/customers/nonexistent-id",
            json={
                "name": "佐藤花子",
                "email": "sato@example.com",
            },
        )

        assert response.status_code == 404

    def test_add_shipping_address(self, client):
        create_response = self._register_customer(
            client, email="addr@example.com"
        )
        customer_id = create_response.json()["customer_id"]

        response = client.post(
            f"/api/v1/customers/{customer_id}/addresses",
            json={
                "label": "会社",
                "postal_code": "150-0001",
                "prefecture": "東京都",
                "city": "渋谷区",
                "street": "渋谷2-2-2",
                "is_default": False,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["label"] == "会社"
        assert data["postal_code"] == "150-0001"

    def test_add_shipping_address_nonexistent_customer_returns_404(
        self, client
    ):
        response = client.post(
            "/api/v1/customers/nonexistent-id/addresses",
            json={
                "label": "会社",
                "postal_code": "150-0001",
                "prefecture": "東京都",
                "city": "渋谷区",
                "street": "渋谷2-2-2",
                "is_default": False,
            },
        )

        assert response.status_code == 404

    def test_list_customer_orders_stub(self, client):
        create_response = self._register_customer(
            client, email="orders@example.com"
        )
        customer_id = create_response.json()["customer_id"]

        response = client.get(
            f"/api/v1/customers/{customer_id}/orders"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0

    def test_list_customer_orders_nonexistent_returns_404(self, client):
        response = client.get(
            "/api/v1/customers/nonexistent-id/orders"
        )

        assert response.status_code == 404
