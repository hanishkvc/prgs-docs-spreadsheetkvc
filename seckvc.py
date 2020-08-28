#!/usr/bin/env python3
# Security from Primitives
# HanishKVC, 2020

import cryptography
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.backends import default_backend
#cryptography.hazmat.primitives.padding


aes=AES(b'KEY_AESALGOKEYSIZE')
cbc = CBC(b'RANDOM_IV_SYMALGOKEYSIZE')
aesCbc=Cipher(aes,cbc,default_backend())
aesCbcEnc=aes_cbc.encryptor()

aesCbcEnc.update(b'123')
aesCbcEnc.update(b'456')
aesCbcEnc.update(b'789')
aesCbcEnc.finalize()

sha256=SHA256()
hmac=HMAC(b'TheKey',sha256,default_backend())



