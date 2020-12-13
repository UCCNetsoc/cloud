
import crypt
import random
import string

def generate(
    length=16
) -> str:
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

def hash(
    password: str
) -> str:
    return crypt.crypt(password, crypt.METHOD_SHA512)