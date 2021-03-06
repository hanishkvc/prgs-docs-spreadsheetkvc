#!/usr/bin/env python3
# Security Recipes from Primitives
# HanishKVC, 2020
#

import cryptography
from cryptography.hazmat.primitives.ciphers.base import Cipher
from cryptography.hazmat.primitives.ciphers.algorithms import AES
from cryptography.hazmat.primitives.ciphers.modes import CBC
from cryptography.hazmat.primitives.hashes import Hash
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.hmac import HMAC
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.padding import PKCS7
from cryptography.hazmat.primitives.kdf import pbkdf2
import os
import base64


bInternalPadder=True
def aes_cbc_enc(aesKey, sPlainMsg):
    '''
    AuthenticatedEncryption - Do a encrypt then mac operation on given message.

        a random iv is generated but not transmitted, instead a random block is
        prepended to the message and encrypted. Inturn the same can be discarded
        during decrypting. Each CBC block depends on the previous encrypted block
        so the 0th block acts as a inplace iv at one level.

        Encryption uses AES in CBC mode with PKCS7 padding where required.
        MAC uses HMAC with SHA256

            As encryption and mac using independent algorithms so the key is
            shared wrt encryption and mac operations.

        With aes length of key passed is independent of the block size used, and
        user can use any valid aes key size.

        This is similar to the age old encrypt as well as sign messages to ensure
        confidentiality as well as authenticity. But then instead of using asymm
        logic for signing, use a hash with hidden key based logic. Also make sure
        that one checks the authenticity before trying to use it or work on it, so
        that new oracles arent opened up, beyond the minimal unavoidable oracle.
    '''
    ### Prepare for encryption
    blockLen = 16
    iv = os.urandom(blockLen)
    aes=AES(aesKey)
    cbc = CBC(iv)
    aesCbc=Cipher(aes,cbc,default_backend())
    aesCbcEnc=aesCbc.encryptor()
    random0thBlock = os.urandom(blockLen)
    # This allows iv to be discarded
    # so also while decrypting discard the 0th block
    plainMsg = random0thBlock + sPlainMsg.encode('utf-8')
    # do PKCS7 padding
    if bInternalPadder:
        padLen = blockLen - (len(plainMsg)%blockLen)
        for i in range(padLen):
            plainMsg += int.to_bytes(padLen,1,'little')
    else:
        pad = PKCS7(blockLen*8).padder()
        plainMsg = pad.update(plainMsg)
        plainMsg += pad.finalize()
    ### do encrypt
    encMsg = aesCbcEnc.update(plainMsg)
    encFina = aesCbcEnc.finalize()
    encMsg = encMsg + encFina
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(encMsg)
    macMsg = hmac.finalize()
    return encMsg, macMsg


def aes_cbc_enc_b64(aesKey, sPlainMsg):
    '''
    AuthenticatedENcryption returning base64 encoded encrypted msg and mac
    '''
    encMsg, macMsg = aes_cbc_enc(aesKey, sPlainMsg)
    encPlusMac = encMsg+macMsg
    return base64.urlsafe_b64encode(encPlusMac)


def aes_cbc_dec(aesKey, bsEncMsg, bsMacMsg):
    '''
    AuthenticatedEncryption - Check mac then decrypt given encrypted message.
    '''
    ### Prepare for mac
    sha256=SHA256()
    hmac=HMAC(aesKey,sha256,default_backend())
    ### do mac
    hmac.update(bsEncMsg)
    macMsg = hmac.finalize()
    if (macMsg != bsMacMsg):
        raise Exception("ERRR:AEDecrypt:Mismatch, skipping")
        return None
    ### Prepare for decryption
    blockLen = 16
    iv = os.urandom(blockLen)
    aes=AES(aesKey)
    cbc = CBC(iv)
    aesCbc=Cipher(aes,cbc,default_backend())
    aesCbcDec=aesCbc.decryptor()
    ### do decrypt
    decMsg = aesCbcDec.update(bsEncMsg)
    decFina = aesCbcDec.finalize()
    decMsg = decMsg + decFina
    # do pkcs7 depadding
    unpad = PKCS7(blockLen*8).unpadder()
    decMsg = unpad.update(decMsg)
    decMsg += unpad.finalize()
    # Discard the initial random block, as corresponding enc and this dec uses
    # non communicated random iv and inturn discardable random 0th block
    decMsg = decMsg[blockLen:]
    return decMsg


def aes_cbc_dec_b64(aesKey, b64EncMacMsg):
    '''
    AuthenticatedENcryption based decryption takes base64 encoded encrypted msg and mac
    '''
    bsEncMac = base64.urlsafe_b64decode(b64EncMacMsg)
    macLen = int(256/8)
    bsEncMsg = bsEncMac[:-macLen]
    bsMac = bsEncMac[-macLen:]
    return aes_cbc_dec(aesKey, bsEncMsg, bsMac)


def get_linekey(lineNum, userKey, fileKey):
    '''
    Get line number specific key by hashing
    userkey, linenum and filekey
    '''
    hasher = Hash(algorithm = SHA256(), backend = default_backend())
    hasher.update(userKey)
    hasher.update(lineNum.to_bytes(4,'little'))
    hasher.update(fileKey)
    key = base64.urlsafe_b64encode(hasher.finalize())
    #print("linekey:{}:{}:{}={}".format(lineNum, userKey, fileKey, key), file=GERRFILE)
    return key


def get_basekeys(filePass, salt):
    '''
    Generate user and file keys from the respective passwords
    and a hopefully random salt.

    user password if not provided, fallsback to a default.
    If provided, it should be readable only by the user and
    not by group or all.
    '''
    # process file password
    kdf = pbkdf2.PBKDF2HMAC(
            algorithm = SHA256(),
            length = 32,
            salt = salt,
            iterations = 186926, # Gandhi+
            backend = default_backend())
    fileKey = base64.urlsafe_b64encode(kdf.derive(bytes(filePass,"utf-8")))
    # get and process user password
    try:
        f = open("~/.config/spreadsheetkvc/userpass")
        l = f.readline()
        userPass = l.strip()
        f.close()
    except:
        userPass = "changemeuser"
    kdf = pbkdf2.PBKDF2HMAC(
            algorithm = SHA256(),
            length = 32,
            salt = salt,
            iterations = 186922, # Gandhi+
            backend = default_backend())
    userKey = base64.urlsafe_b64encode(kdf.derive(bytes(userPass,"utf-8")))
    return userKey, fileKey


def test_101():
    sPlainMsg = "hello world"
    bsEncMsg, bsMac = aes_cbc_enc(b'0123456789abcdef', sPlainMsg)
    sDecMsg = aes_cbc_dec(b'0123456789abcdef', bsEncMsg, bsMac)
    print("DBUG:Normal:\n\tsPlainMsg:{}:{}\n\tencMsg:{}:{}\n\tMacMsg:{}:{}\n\tdecMsg:{}:{}".format(len(sPlainMsg), sPlainMsg, len(bsEncMsg), bsEncMsg, len(bsMac), bsMac, len(sDecMsg), sDecMsg))

    print("DBUG:Wrong Key")
    print(aes_cbc_dec(b'0123456789abcdee', bsEncMsg, bsMac))

    print("DBUG:Modified EncData")
    bsCrptEncMsg = bytearray(bsEncMsg)
    bsCrptEncMsg[3] = 99
    print(aes_cbc_dec(b'0123456789abcdef', bytes(bsCrptEncMsg), bsMac))

    print("DBUG:Modified Mac")
    bsCrptMac = bytearray(bsMac)
    savedMacByte = bsCrptMac[3]
    bsCrptMac[3] = 99
    print(aes_cbc_dec(b'0123456789abcdef', bsEncMsg, bytes(bsCrptMac)))

    print("DBUG:BackTo proper key,encMsg,mac")
    bsCrptMac[3] = savedMacByte
    print(aes_cbc_dec(b'0123456789abcdef', bsEncMsg, bytes(bsCrptMac)))


    sPlainMsg = "new world"
    b64EncMac = aes_cbc_enc_b64(b'0123456789abcdef', sPlainMsg)
    sDecMsg = aes_cbc_dec_b64(b'0123456789abcdef', b64EncMac)
    print("DBUG:Base64:\n\tsPlainMsg:{}:{}\n\tencMac:{}:{}\n\tdecMsg:{}:{}".format(len(sPlainMsg), sPlainMsg, len(b64EncMac), b64EncMac, len(sDecMsg), sDecMsg))
    sDecMsg = aes_cbc_dec_b64(b'0123456789abcdee', b64EncMac)


# vim: set sts=4 expandtab: #
