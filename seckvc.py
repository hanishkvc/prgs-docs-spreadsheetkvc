#!/usr/bin/env python3
# Security Recipes from Primitives
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
import base64


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
    print("DBUG:AesCbcEnc:Msg2Enc:{}:{}".format(len(plainMsg),plainMsg))
    encMsg = aesCbcEnc.update(plainMsg)
    encFina = aesCbcEnc.finalize()
    encMsg = encMsg + encFina
    print("DBUG:AesCbcEnc:EncMsg:{}:{}".format(len(encMsg),encMsg))
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(encMsg)
    macMsg = hmac.finalize()
    print("DBUG:AesCbcEnc:MacMsg:{}".format(macMsg))
    return encMsg, macMsg


def aes_cbc_enc_b64(aesKey, sPlainMsg):
    '''
    AuthenticatedENcryption returning base64 encoded encrypted msg and mac
    '''
    encMsg, macMsg = aes_cbc_enc(aesKey, sPlainMsg)
    return base64.urlsafe_b64encode(encMsg), base64.urlsafe_b64encode(macMsg)


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
    print("DBUG:AesCbcDec:MacMsg:{}={}".format(macMsg, bsMacMsg))
    if (macMsg != bsMacMsg):
        print("DBUG:AesCbcDec: MAC Mismatch, bailing out")
        return None
    ### do decrypt
    print("DBUG:AesCbcDec:Msg2Dec:{}:{}".format(len(bsEncMsg),bsEncMsg))
    decMsg = aesCbcDec.update(bsEncMsg)
    decFina = aesCbcDec.finalize()
    decMsg = decMsg + decFina
    print("DBUG:AesCbcDec:DecMsg:{}:{}".format(len(decMsg),decMsg))
    # Discard the initial random block, as corresponding enc and this dec uses
    # non communicated random iv and inturn discardable random 0th block
    decMsg = decMsg[blockLen:]
    return decMsg


def aes_cbc_dec_b64(aesKey, b64EncMsg, b64MacMsg):
    '''
    AuthenticatedENcryption based decryption takes base64 encoded encrypted msg and mac
    '''
    bsEncMsg = base64.urlsafe_b64decode(b64EncMsg)
    bsMac = base64.urlsafe_b64decode(b64MacMsg)
    return aes_cbc_dec(aesKey, bsEncMsg, bsMac)


bsEncMsg, bsMac = aes_cbc_enc(b'0123456789abcdef', "hello world")
sDecMsg = aes_cbc_dec(b'0123456789abcdee', bsEncMsg, bsMac)
sDecMsg = aes_cbc_dec(b'0123456789abcdef', bsEncMsg, bsMac)
print("DBUG:decMsg:{}".format(sDecMsg))

b64EncMsg, b64Mac = aes_cbc_enc_b64(b'0123456789abcdef', "new world")
print("DBUG:b64EncMsg:{}:b64Mac:{}".format(b64EncMsg, b64Mac))
sDecMsg = aes_cbc_dec_b64(b'0123456789abcdee', b64EncMsg, b64Mac)
sDecMsg = aes_cbc_dec_b64(b'0123456789abcdef', b64EncMsg, b64Mac)
print("DBUG:decMsg:{}".format(sDecMsg))


# vim: set sts=4 expandtab: #
