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


def aes_cbc_enc(aesKey, sPlainMsg):
    '''
    AuthenticatedEncryption - Do a encrypt then mac operation on given message.
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
    plainMsg = random0thBlock + sPlainMsg.encode('utf-8')
    padLen = blockLen - (len(plainMsg)%blockLen)
    # Space padding will do in this particular usecase
    for i in range(padLen):
        plainMsg += b' '
    ### do encrypt
    print("DBUG:Msg2Enc:{}:{}".format(len(plainMsg),plainMsg))
    encMsg = aesCbcEnc.update(plainMsg)
    encFina = aesCbcEnc.finalize()
    encMsg = encMsg + encFina
    print("DBUG:EncMsg:{}:{}".format(len(encMsg),encMsg))
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(encMsg)
    macMsg = hmac.finalize()
    print("DBUG:MacMsg:{}".format(macMsg))
    return encMsg, macMsg


def aes_cbc_dec(aesKey, bsEncMsg, bsMacMsg):
    '''
    AuthenticatedEncryption - Check mac then decrypt given encrypted message.
    '''
    ### Prepare for decryption
    blockLen = len(aesKey)
    iv = os.urandom(blockLen)
    aes=AES(aesKey)
    cbc = CBC(iv)
    aesCbc=Cipher(aes,cbc,default_backend())
    aesCbcDec=aesCbc.decryptor()
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(bsEncMsg)
    macMsg = hmac.finalize()
    print("DBUG:MacMsg:{}={}".format(macMsg, bsMacMsg))
    ### do decrypt
    print("DBUG:Msg2Dec:{}:{}".format(len(bsEncMsg),bsEncMsg))
    decMsg = aesCbcDec.update(bsEncMsg)
    decFina = aesCbcDec.finalize()
    decMsg = decMsg + decFina
    print("DBUG:DecMsg:{}:{}".format(len(decMsg),decMsg))
    return decMsg



bsEncMsg, bsMac = aes_cbc_enc(b'0123456789abcdef', "hello world")
sDecMsg = aes_cbc_dec(b'0123456789abcdef', bsEncMsg, bsMac)



# vim: set sts=4 expandtab: #
