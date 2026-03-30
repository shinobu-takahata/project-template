import pytest

from app.domain.customer.value_objects.address import Address
from app.domain.customer.value_objects.customer_id import CustomerId
from app.domain.customer.value_objects.customer_name import CustomerName
from app.domain.customer.value_objects.email_address import EmailAddress
from app.domain.customer.value_objects.member_rank import MemberRank


class TestCustomerId:
    def test_create_valid_id(self):
        cid = CustomerId("test-id")
        assert cid.value == "test-id"

    def test_generate_unique_id(self):
        id1 = CustomerId.generate()
        id2 = CustomerId.generate()
        assert id1.value != id2.value

    def test_empty_id_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            CustomerId("")

    def test_whitespace_id_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            CustomerId("   ")


class TestCustomerName:
    def test_create_valid_name(self):
        name = CustomerName("田中太郎")
        assert name.value == "田中太郎"

    def test_empty_name_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            CustomerName("")

    def test_too_long_name_raises_error(self):
        with pytest.raises(ValueError, match="100 characters or less"):
            CustomerName("a" * 101)

    def test_max_length_name(self):
        name = CustomerName("a" * 100)
        assert len(name.value) == 100


class TestEmailAddress:
    def test_create_valid_email(self):
        email = EmailAddress("test@example.com")
        assert email.value == "test@example.com"

    def test_empty_email_raises_error(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            EmailAddress("")

    def test_invalid_format_raises_error(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            EmailAddress("not-an-email")

    def test_missing_at_raises_error(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            EmailAddress("testexample.com")

    def test_missing_domain_raises_error(self):
        with pytest.raises(ValueError, match="Invalid email format"):
            EmailAddress("test@")

    def test_too_long_email_raises_error(self):
        with pytest.raises(ValueError, match="255 characters or less"):
            EmailAddress("a" * 250 + "@example.com")

    def test_valid_email_with_plus(self):
        email = EmailAddress("test+tag@example.com")
        assert email.value == "test+tag@example.com"


class TestMemberRank:
    def test_default_rank_is_bronze(self):
        assert MemberRank.default() == MemberRank.BRONZE

    def test_rank_values(self):
        assert MemberRank.BRONZE.value == "BRONZE"
        assert MemberRank.SILVER.value == "SILVER"
        assert MemberRank.GOLD.value == "GOLD"

    def test_create_from_string(self):
        rank = MemberRank("GOLD")
        assert rank == MemberRank.GOLD


class TestAddress:
    def test_create_valid_address(self):
        addr = Address(
            postal_code="100-0001",
            prefecture="東京都",
            city="千代田区",
            street="千代田1-1-1",
        )
        assert addr.postal_code == "100-0001"
        assert addr.prefecture == "東京都"

    def test_invalid_postal_code_raises_error(self):
        with pytest.raises(ValueError, match="NNN-NNNN format"):
            Address(
                postal_code="1234567",
                prefecture="東京都",
                city="千代田区",
                street="千代田1-1-1",
            )

    def test_postal_code_without_hyphen_raises_error(self):
        with pytest.raises(ValueError, match="NNN-NNNN format"):
            Address(
                postal_code="1000001",
                prefecture="東京都",
                city="千代田区",
                street="千代田1-1-1",
            )

    def test_empty_prefecture_raises_error(self):
        with pytest.raises(ValueError, match="Prefecture cannot be empty"):
            Address(
                postal_code="100-0001",
                prefecture="",
                city="千代田区",
                street="千代田1-1-1",
            )

    def test_empty_city_raises_error(self):
        with pytest.raises(ValueError, match="City cannot be empty"):
            Address(
                postal_code="100-0001",
                prefecture="東京都",
                city="",
                street="千代田1-1-1",
            )

    def test_empty_street_raises_error(self):
        with pytest.raises(ValueError, match="Street cannot be empty"):
            Address(
                postal_code="100-0001",
                prefecture="東京都",
                city="千代田区",
                street="",
            )

    def test_too_long_prefecture_raises_error(self):
        with pytest.raises(ValueError, match="10 characters or less"):
            Address(
                postal_code="100-0001",
                prefecture="a" * 11,
                city="千代田区",
                street="千代田1-1-1",
            )

    def test_address_is_immutable(self):
        addr = Address(
            postal_code="100-0001",
            prefecture="東京都",
            city="千代田区",
            street="千代田1-1-1",
        )
        with pytest.raises(AttributeError):
            addr.postal_code = "200-0002"
