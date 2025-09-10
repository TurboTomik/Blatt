import pytest

from users.forms import UserLoginForm, UserRegisterForm
from users.models import User


class TestUserRegisterForm:
    """
    Test suite for UserRegisterForm validation and behavior.

    Tests cover:
    - Valid form submissions
    - Field validation (username, email, passwords)
    - Cross-field validation (password matching)
    - Edge cases and error handling
    - Security considerations
    """

    def test_valid_registration_form(self):
        """Test that valid form data passes validation."""
        form_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": "securepassword.123",
            "password2": "securepassword.123",
        }

        form = UserRegisterForm(data=form_data)

        assert form.is_valid() is True

        assert form.cleaned_data["username"] == "newuser"
        assert form.cleaned_data["email"] == "newuser@example.com"
        assert form.cleaned_data["password1"] == "securepassword.123"

    @pytest.mark.parametrize(
        "username",
        [
            "user123",
            "test_user",
            "a" * 30,
        ],
    )
    def test_valid_username(self, username):
        """Test that valid username passes validation."""
        base_data = {
            "email": "test@example.com",
            "password1": "securepass.123",
            "password2": "securepass.123",
        }

        form = UserRegisterForm(data={**base_data, "username": username})
        assert form.is_valid()
        assert "username" not in form.errors

    @pytest.mark.parametrize(
        "username",
        [
            "user-name",  # Hyphen not allowed
            "user@name",  # @ not allowed
            "user name",  # Space not allowed
            "user.name",  # Dot not allowed
            "user#123",  # Special chars not allowed
            "_user123",  # Begin with underscore
            "user123_",  # End with underscore
            "user____123",  # Consecutive underscores
            "a" * 31,  # Too long (> 30 chars)
            "us",  # Too short (< 3 chars)
        ],
    )
    def test_invalid_username(self, username):
        """Test that invalid username doesn't pass validation."""
        base_data = {
            "email": "test@example.com",
            "password1": "securepass.123",
            "password2": "securepass.123",
        }

        form = UserRegisterForm(data={**base_data, "username": username})
        assert not form.is_valid()
        if 3 <= len(username) <= 100:
            assert "username" in form.errors

    @pytest.mark.parametrize(
        "email",
        [
            "user@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "very.long.email.address@very.long.domain.example.com",
        ],
    )
    def test_valid_email(self, email):
        """Test that valid email passes validation."""
        base_data = {
            "username": "testuser",
            "password1": "securepass.123",
            "password2": "securepass.123",
        }

        form = UserRegisterForm(data={**base_data, "email": email})
        assert form.is_valid()
        assert "email" not in form.errors

    @pytest.mark.parametrize(
        "email",
        [
            "notanemail",
            "user@",
            "@example.com",
            "user space@example.com",
            "user@example",
            "a" * 250 + "@example.com",
        ],
    )
    def test_invalid_email(self, email):
        """Test that invalid email doesn't pass validation."""
        base_data = {
            "username": "testuser",
            "password1": "securepass.123",
            "password2": "securepass.123",
        }

        form = UserRegisterForm(data={**base_data, "email": email})
        assert not form.is_valid()
        assert "email" in form.errors

    @pytest.mark.parametrize(
        "password",
        [
            "password.123",
            "PassWord!4",
            ".Password1",
            "PASSWORD.88005553535",
        ],
    )
    def test_valid_password(self, password):
        """Test that valid password passes validation."""
        base_data = {
            "username": "testuser",
            "email": "test@example.com",
        }

        form_data = {**base_data, "password1": password, "password2": password}
        form = UserRegisterForm(data=form_data)
        assert form.is_valid()
        assert "password1" not in form.errors

    @pytest.mark.parametrize(
        "password",
        [
            "password",  # only letters
            "12345678",  # only numeric
            "abc123",  # Too short
            "abcde123",  # without special symbols
        ],
    )
    def test_invalid_password(self, password):
        """Test that invalid password doesn't pass validation."""
        base_data = {
            "username": "testuser",
            "email": "test@example.com",
        }

        form_data = {**base_data, "password1": password, "password2": password}
        form = UserRegisterForm(data=form_data)
        assert not form.is_valid()
        assert "password1" in form.errors
        assert "password2" in form.errors

    def test_password_mismatch(self):
        """Test that mismatched passwords are rejected."""
        form_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password1": "securepassword.123",
            "password2": "differentpassword.123",
        }

        form = UserRegisterForm(data=form_data)
        assert not form.is_valid()
        assert "__all__" in form.errors
        assert "match" in str(form.errors["__all__"][0]).lower()

    def test_empty_fields(self):
        """Test that required fields cannot be empty."""
        form = UserRegisterForm(data={})
        assert not form.is_valid()

        required_fields = ["username", "email", "password1", "password2"]
        for field in required_fields:
            assert field in form.errors

    def test_whitespace_handling(self):
        """Test that whitespace in fields is handled correctly."""
        form_data = {
            "username": "   testuser   ",
            "email": "   test@example.com   ",
            "password1": "securepass.123",
            "password2": "securepass.123",
        }

        form = UserRegisterForm(data=form_data)
        assert form.is_valid()

        assert form.cleaned_data["username"] == "testuser"
        assert form.cleaned_data["email"] == "test@example.com"


class TestUserLoginForm:
    """
    Test suite for UserLoginForm validation and behavior.

    Tests cover:
    - Valid form submissions
    - Field validation
    - Input normalization
    - Error handling
    - Edge cases
    """

    @pytest.fixture
    def user(self):
        """Fixture to create a user instance."""
        User.objects.create_user(
            username="testuser", email="test@example.com", password="testpassword.123"
        )

    def test_valid_login_form(self):
        """Test that valid form data passes validation."""
        form_data = {"username": "testuser", "password": "testpassword.123"}

        form = UserLoginForm(data=form_data)
        assert form.is_valid()

        assert form.cleaned_data["username"] == "testuser"
        assert form.cleaned_data["password"] == "testpassword.123"

    def test_email_as_username(self):
        """Test that email can be used as username in login form."""
        form_data = {
            "username": "test@example.com",
            "password": "testpassword123",
        }

        form = UserLoginForm(data=form_data)
        assert form.is_valid()
        assert form.cleaned_data["username"] == "test@example.com"

    def test_empty_fields(self):
        """Test that required fields cannot be empty."""
        form = UserLoginForm(data={})
        assert not form.is_valid()

        assert "username" in form.errors
        assert "password", form.errors

    def test_empty_username(self):
        """Test handling of empty username field."""
        form_data = {"username": "", "password": "testpassword123"}

        form = UserLoginForm(data=form_data)
        assert not form.is_valid()
        assert "username" in form.errors

    def test_empty_password(self):
        """Test handling of empty password field."""
        form_data = {"username": "testuser", "password": ""}

        form = UserLoginForm(data=form_data)
        assert not form.is_valid()
        assert "password" in form.errors

    def test_whitespace_handling(self):
        """Test that whitespace in fields is handled correctly."""
        form_data = {
            "username": "  testuser  ",  # Spaces around username
            "password": "testpassword123",
        }

        form = UserLoginForm(data=form_data)
        assert form.is_valid()

        assert form.cleaned_data["username"] == "testuser"

    def test_long_username_field(self):
        """Test maximum length validation for username field."""
        long_username = "a" * 251  # Exceeds max_length=250

        form_data = {"username": long_username, "password": "testpassword123"}

        form = UserLoginForm(data=form_data)
        assert not form.is_valid()
        assert "username" in form.errors

    def test_password_length_validation(self):
        """Test password length validation."""
        form_data = {
            "username": "testuser",
            "password": "1234567",  # 7 chars, minimum is 8
        }

        form = UserLoginForm(data=form_data)
        assert not form.is_valid()
        assert "password" in form.errors

        form_data["password"] = "a" * 129  # Exceeds max_length=128
        form = UserLoginForm(data=form_data)
        assert not form.is_valid()
        assert "password" in form.errors


class TestFormSecurity:
    """
    Test suite for security-related form behavior.

    Tests cover:
    - Input sanitization
    - XSS prevention
    - SQL injection prevention
    - Unicode handling
    """

    def test_unicode_input_handling(self):
        """Test that forms handle Unicode input correctly."""
        form_data = {
            "username": "тестユーザー123",  # Cyrillic + Japanese + ASCII  # noqa: RUF001
            "email": "тест@пример.com",
            "password1": "пароль123測試",  # noqa: RUF001
            "password2": "пароль123測試",  # noqa: RUF001
        }

        form = UserRegisterForm(data=form_data)
        try:
            form.is_valid()
        except Exception as e:
            pytest.fail(f"Form should handle Unicode input without crashing: {e}")

    @pytest.mark.parametrize(
        "malicious_input",
        [
            '<script>alert("xss")</script>',
            '<img src="x" onerror="alert(1)">',
            '"><script>alert(document.cookie)</script>',
        ],
    )
    def test_html_injection_prevention(self, malicious_input):
        """Test that HTML/script tags in input are handled safely."""
        form_data = {
            "username": malicious_input,
            "email": "test@example.com",
            "password1": "securepass123",
            "password2": "securepass123",
        }

        form = UserRegisterForm(data=form_data)
        try:
            form.is_valid()
            if form.is_valid():
                assert "<script>" not in form.cleaned_data.get("username", "")
        except Exception as e:
            pytest.fail(f"Form should handle malicious input safely: {e}")

    @pytest.mark.parametrize(
        "sql_input",
        [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users --",
        ],
    )
    def test_sql_injection_prevention(self, sql_input):
        """Test that SQL injection attempts are handled safely."""
        form_data = {"username": sql_input, "password": "testpass123"}

        form = UserLoginForm(data=form_data)
        try:
            form.is_valid()
        except Exception as e:
            pytest.fail(f"Form should handle SQL injection attempts safely: {e}")
