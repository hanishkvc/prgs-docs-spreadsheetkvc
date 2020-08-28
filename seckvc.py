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
import os


def aes_cbc_enc(aesKey, plainMsg):
    '''
    Do a encrypt then mac operation on given message.
    '''
    ### Prepare for encryption
    blockLen = len(aesKey)
    iv = os.urandom(blockLen)
    aes=AES(aesKey)
    cbc = CBC(iv)
    aesCbc=Cipher(aes,cbc,default_backend())
    aesCbcEnc=aesCbc.encryptor()
    random0thBlock = os.urandom(blockLen)
    # This allows iv to be discarded
    # so also while decrypting discard the 0th block
    plainMsg = random0thBlock + plainMsg
    padLen = blockLen - (len(plainMsg)%blockLen)
    # Space padding will do in this particular usecase
    for i in range(padLen):
        plainMsg += ' '
    ### do encrypt
    aesCbcEnc.update(plainMsg)
    encMsg = aesCbcEnc.finalize()
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(encMsg)
    macMsg = hmac.finalize()
    return encMsg, macMsg


print(aes_cbc_enc(b'0123456789abcdef', "hello world"))




# vim: set sts=4 expandtab: #
