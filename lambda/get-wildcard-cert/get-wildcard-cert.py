import json
import os
import sys
from datetime import datetime
from urllib.request import urlopen, Request

from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, ec
import boto3
import requests


class ACMERequestAgent:
    DEFAULT_DIRECTORY_URL = 'https://acme-v02.api.letsencrypt.org/directory'
    REQUEST_HEADER = {
        'Content-Type': 'application/jose+json',
        'User-Agent': 'CertRequest Lambda/0.9'
    }

    def __init__(self):
        super().__init__()

    def _do_request(self, data: dict):
        resp = requests.post(
            self.DEFAULT_DIRECTORY_URL,
            data=data,
            headers=self.REQUEST_HEADER
        )
        resp.raise_for_status()

    def _send_signed_request(self, payload: str):
        if isinstance(payload, str):
            payload = bytes(payload, 'utf-8')
        pass


class KeyGenerator:
    RSA_KEY_SIZE = 3072

    def __init__(self):
        self.privkey = None
        self.csr = None
        self.csr_cn = ''

    def generate_private_key(self, key_type = ''):
        if key_type == 'ec' or key_type == 'ecdsa':
            self.privkey = ec.generate_private_key(
                ec.SECP256R1(),
                default_backend()
            )
        else:
            self.privkey = rsa.generate_private_key(
                public_exponent=65537,
                key_size=self.RSA_KEY_SIZE,
                backend=default_backend()
            )

    def write_privkey_to_file(self, filename):
        serialized_key = self.privkey.private_bytes(
                serialization.Encoding.PEM,
                serialization.PrivateFormat.PKCS8,
                serialization.NoEncryption()
        )
        with open(filename, 'wb') as fpw:
            fpw.write(serialized_key)

    def read_from_file(self, filename):
        with open(filename, 'rb') as fpr:
            self.privkey = serialization.load_pem_private_key(
                fpr.read(),
                password=None,
                backend=default_backend()
            )

    def make_csr(self):
        builder = x509.CertificateSigningRequestBuilder()
        builder = builder.subject_name(
            x509.Name([
                x509.NameAttribute(x509.NameOID.COMMON_NAME, self.csr_cn),
            ])
        )
        self.csr = builder.sign(privkey, hashes.SHA256(), default_backend())

    def write_csr_to_file(self, filename):
        serialized_cert = csr.public_bytes(
            serialization.Encoding.PEM
        )
        with open(filename, 'wb') as fpw:
            fpw.write(serialized_cert)


class Route53Modifier:

    def __init__(self):
        super().__init__()


def json_dt(o):
    if isinstance(o, datetime):
        return o.isoformat()

def lambda_handler(event, context) -> str:
    pass


if __name__ == "__main__":
    context = dict()
    event = {
        'detail': {
            'state': sys.argv[1],
            'instance-id': sys.argv[2]
        }
    }
    lambda_handler(event, context)
