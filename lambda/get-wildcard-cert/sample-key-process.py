from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa, ec, ed25519
from cryptography.hazmat.primitives import hashes, serialization


def make_privkey(key_type):
    if key_type == 'ec' or key_type == 'ecdsa':
        privkey = ec.generate_private_key(
            ec.SECP256R1(),
            default_backend()
        )
    elif key_type == 'ed25519':
        privkey = ed25519.Ed25519PrivateKey.generate()
    else:
        privkey = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
    return privkey

def save_privkey(filename, privkey):
    serialized_key = privkey.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption()
    )
    with open(filename, 'wb') as fpw:
        fpw.write(serialized_key)

def load_privkey(filename):
    with open(filename, 'rb') as fpr:
        privkey = serialization.load_pem_private_key(
            fpr.read(),
            password=None,
            backend=default_backend()
        )
    return privkey

def save_pubkey(filename, privkey):
    pubkey = privkey.public_key()
    serialized_key = pubkey.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with open(filename, 'wb') as fpw:
        fpw.write(serialized_key)

def make_csr(privkey):
    builder = x509.CertificateSigningRequestBuilder()
    builder = builder.subject_name(
        x509.Name([
            x509.NameAttribute(x509.NameOID.COMMON_NAME, 'example.com'),
        ])
    )
    builder = builder.add_extension(
        x509.SubjectAlternativeName([
            x509.DNSName('www.example.com'),
            x509.DNSName('test.example.com')
            ]
        ),
        critical=False
    )
    return builder.sign(privkey, hashes.SHA256(), default_backend())

def save_csr(filename, csr):
    serialized_cert = csr.public_bytes(
        serialization.Encoding.PEM
    )
    with open(filename, 'wb') as fpw:
        fpw.write(serialized_cert)


if __name__ == "__main__":
    rsa_key = make_privkey('rsa')
    ecdsa_key = make_privkey('ecdsa')

    csr_rsa = make_csr(rsa_key)
    save_csr('sample.rsa.csr', csr_rsa)
    csr_ecdsa = make_csr(ecdsa_key)
    save_csr('sample.ecdsa.csr', csr_ecdsa)
