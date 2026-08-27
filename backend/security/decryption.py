import os

from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from backend.settings import get_settings
from backend.security.encryption import encrypt_text

# load_dotenv()

# AES_SECRET = os.getenv("LOCAL_AES_SECRET_KEY")

# if not AES_SECRET:
#     raise RuntimeError(
#         "LOCAL_AES_SECRET_KEY is not configured"
#     )

# AES_KEY = bytes.fromhex(AES_SECRET)

def _aes_key() -> bytes:
    value = get_settings().local_aes_secret_key

    try:
        key = bytes.fromhex(value)
    except ValueError as exc:
        raise RuntimeError(
            "LOCAL_AES_SECRET_KEY must be hexadecimal"
        ) from exc

    if len(key) != 32:
        raise RuntimeError(
            "LOCAL_AES_SECRET_KEY must represent 32 bytes"
        )

    return key


# def decrypt_field(encrypted_binary) -> str:

#     if not encrypted_binary:
#         return ""

#     data = bytes(encrypted_binary)

#     print("Encrypted data length:", len(data))
#     print("First 20 bytes:", data[:20])
#     print("AES key length:", len(AES_KEY))

#     if len(data) < 28:
#         raise ValueError("Invalid encrypted data")

#     nonce = data[:12]
#     ciphertext = data[12:]

#     print("Nonce length:", len(nonce))
#     print("Ciphertext length:", len(ciphertext))

#     aesgcm = AESGCM(AES_KEY)

#     decrypted_bytes = aesgcm.decrypt(
#         nonce,
#         ciphertext,
#         None
#     )

#     return decrypted_bytes.decode("utf-8")

# def decrypt_field(encrypted_value) -> str:
#     if not encrypted_value:
#         return ""

#     data = bytes(encrypted_value)

#     value = data.decode("utf-8")

#     if value.startswith("encrypted_"):
#         return value[len("encrypted_"):]

#     return value


def decrypt_field(encrypted_binary) -> str:

    if not encrypted_binary:
        return ""

    data = bytes(encrypted_binary)


    if len(data) < 28:
        raise ValueError("Invalid encrypted data")

    nonce = data[:12]
    ciphertext = data[12:]

    aesgcm = AESGCM(_aes_key())

    decrypted_bytes = aesgcm.decrypt(
        nonce,
        ciphertext,
        None
    )

    return decrypted_bytes.decode("utf-8")


if __name__=="__main__":

    

    test_value = "TEST USER"

    encrypted = encrypt_text(test_value)

    print("========== AES ROUND TRIP TEST ==========")
    print("Original:", test_value)

    decrypted = decrypt_field(encrypted)

    print("Decrypted:", decrypted)
    print("Match:", test_value == decrypted)
    print("=========================================")