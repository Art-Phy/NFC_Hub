
from argon2 import PasswordHasher, Type

from nfc_hub.core.passwords import hash_password, password_needs_rehash, verify_password



class TestHashPassword:
    def test_hash_uses_argon2id(self):
        password_hash = hash_password("correct horse battery staple")

        assert password_hash.startswith("$argon2id$")


    def test_same_password_produces_different_hashes(self):
        password = "correct horse battery staple"

        first_hash = hash_password(password)
        second_hash = hash_password(password)

        assert first_hash != second_hash



class TestVerifyPassword:
    def test_correct_password_verifies(self):
        password = "correct horse battery staple"
        password_hash = hash_password(password)

        assert verify_password(password, password_hash) is True


    def test_incorrect_password_does_not_verify(self):
        password_hash = hash_password("correct password")

        assert verify_password("incorrect password", password_hash) is False


    def test_invalid_hash_does_not_verify(self):
        assert verify_password("password", "not-a-valid-hash") is False



class TestPasswordNeedsRehash:
    def test_current_hash_does_not_need_rehash(self):
        password_hash = hash_password("correct horse bttery staple")

        assert password_needs_rehash(password_hash) is False


    def test_hash_with_old_parameters_needs_rehash(self):
        old_hasher = PasswordHasher(
            memory_cost=8_192,
            time_cost =1,
            parallelism=1,
            type=Type.ID,
        )
        password_hash = old_hasher.hash("correct horse battery staple")

        assert password_needs_rehash(password_hash) is True


    def test_invalid_hash_needs_rehash(self):
        assert password_needs_rehash("not-a-valid-hash") is True
