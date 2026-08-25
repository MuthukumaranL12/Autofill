import os

from dotenv import load_dotenv
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

load_dotenv()

AES_SECRET = os.getenv("LOCAL_AES_SECRET_KEY")

if not AES_SECRET:
    raise RuntimeError(
        "LOCAL_AES_SECRET_KEY is not configured"
    )

AES_KEY = bytes.fromhex(AES_SECRET)


# def decrypt_field(encrypted_binary) -> str:

#     if not encrypted_binary:
#         return ""

#     data = bytes(encrypted_binary)

#     print("Encrypted data length:", len(data))
#     print("First 20 bytes:", data[:20])
#     print("AES key length:", len(AES_KEY))

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

def decrypt_field(encrypted_value) -> str:
    if not encrypted_value:
        return ""

    data = bytes(encrypted_value)

    value = data.decode("utf-8")

    if value.startswith("encrypted_"):
        return value[len("encrypted_"):]

    return value