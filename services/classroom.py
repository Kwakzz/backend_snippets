import secrets
import string

def generate_class_code(length=7) -> str:
    chars = string.ascii_uppercase + string.digits
    code = ''.join(secrets.choice(chars) for _ in range(length))
    return code