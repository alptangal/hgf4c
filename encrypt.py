from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
import os,subprocess
from dotenv import load_dotenv
import base64
import time
import traceback
from random import choice
import string
load_dotenv()

def generate_random_string(length):
    if length <= 0:
        raise ValueError("Length must be a positive integer.")

    characters = string.ascii_letters + string.digits
    return ''.join(choice(characters) for _ in range(length))

def encrypt_file(file_path, encrypted_file_path, secret_key, iv):
    with open(file_path, 'rb') as file:
        plaintext = file.read()
    padder = padding.PKCS7(algorithms.AES.block_size).padder()
    padded_data = padder.update(plaintext) + padder.finalize()
    cipher = Cipher(algorithms.AES(secret_key), modes.CBC(iv), backend=default_backend())
    encryptor = cipher.encryptor()
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    with open(encrypted_file_path, 'wb') as encrypted_file:
        encrypted_file.write(ciphertext)
def decrypt_file(encrypted_file_path, decrypted_file_path, secret_key, iv):
    with open(encrypted_file_path, 'rb') as encrypted_file:
        ciphertext = encrypted_file.read()
    cipher = Cipher(algorithms.AES(secret_key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(algorithms.AES.block_size).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    with open(decrypted_file_path, 'wb') as decrypted_file:
        decrypted_file.write(plaintext)

def do_encrypt(input_file,output_file,secret_key,iv):
    encrypt_file(input_file,output_file,secret_key,iv)
    return output_file
