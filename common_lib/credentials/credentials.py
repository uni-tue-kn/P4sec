import sys

# common
from common_lib.exception import FileNotFound

# protobuf
from credentials_pb2 import credentials # type: ignore

# other
from os import path
from grpc import ssl_server_credentials, ssl_channel_credentials # type: ignore
from typing import Dict
from OpenSSL import crypto # type: ignore

class Credentials:

    def __init__(self, ca, cert, key):
        self.ca = ca
        self.cert = cert
        self.key = key

    @classmethod
    def generate(Class):
        # TODO generate credentials
        #ca_key = crypto.PKey()
        #ca_key.generate_key(crypto.TYPE_RSA, 4096)

        #ca_cert = crypto.X509()
        #ca_cert.set_pubkey(ca_key)
        #ca_cert.sign(ca_key, "sha256")

        #ca = crypto.dump_certificate(crypto.FILETYPE_PEM, ca_cert)

        #client_key = crypto.PKey()
        #client_key.generate_key(crypto.TYPE_RSA, 4096)
        #client_cert = crypto.X509()
        #client_cert.set_pubkey(client_key)
        #client_cert.sign(ca_key, "sha256")

        #cert = crypto.dump_certificate(crypto.FILETYPE_PEM, client_cert)
        #key = crypto.dump_privatekey(crypto.FILETYPE_PEM, client_key)

        #return Class(ca, cert, key)
        return Class.read(
            path.join(path.dirname(__file__), "../../build/certificates/ca.crt"),
            path.join(path.dirname(__file__), "../../build/certificates/localhost.crt"),
            path.join(path.dirname(__file__), "../../build/certificates/localhost.key")
        )

    def get_server_credentials(self):
        return ssl_server_credentials([(self.key, self.cert)], self.ca, True)

    def get_client_credentials(self):
        return ssl_channel_credentials(self.ca, self.key, self.cert)

    @staticmethod
    def read_file(path):
        try:
            if sys.version_info >= (3, 0):
                return bytes(open(path).read(), "utf-8")
            else:
                return open(path).read()
        except IOError:
            raise FileNotFound(path)


    @classmethod
    def read(Class, ca_path, cert_path, key_path):
        ca   = Credentials.read_file(ca_path)
        cert = Credentials.read_file(cert_path)
        key  = Credentials.read_file(key_path)
        return Class(ca, cert, key)

    @classmethod
    def read_from(Class, data: Dict):
        return Class.read(data["ca-file"], data["cert-file"], data["key-file"])

    def to_proto(self) -> credentials:
        proto = credentials()
        proto.ca = self.ca
        proto.cert = self.cert
        proto.key = self.key
        return proto

    @classmethod
    def from_proto(Class, proto: credentials):
        ca = proto.ca
        cert = proto.cert
        key = proto.key
        return Class(ca, cert, key)
