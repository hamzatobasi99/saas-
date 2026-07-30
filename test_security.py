from app.core.security import encrypt_token, decrypt_token

original = "EAABxxxxxxxxxxxxxxxxx_META_TOKEN"
encrypted = encrypt_token(original)
decrypted = decrypt_token(encrypted)

print(f"🔑 النص الأصلي: {original}")
print(f"🔒 بعد التشفير: {encrypted}")
print(f"🔓 بعد فك التشفير: {decrypted}")

assert original == decrypted, "❌ التشفير غير متطابق!"
print("✅ موديول التشفير يعمل بنجاح 100%!")