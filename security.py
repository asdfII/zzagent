# -*- coding: utf-8 -*-
#openssl req -new -x509 -days 365 -nodes -out server_cert.pem -keyout server_key.pem
#openssl req -new -x509 -days 365 -nodes -out client_cert.pem -keyout client_key.pem


import ssl


class SSLMixin(object):
    def __init__(self, keyfile=None, certfile=None,
        ca_certs=None, cert_reqs=ssl.CERT_NONE, *args, **kwargs):
        self._keyfile = keyfile
        self._certfile = certfile
        self._ca_certs = ca_certs
        self._cert_reqs = cert_reqs
        super().__init__(*args, **kwargs)
    
    def get_request(self):
        client, addr = super().get_request()
        client_ssl = ssl.wrap_socket(client,
            keyfile = self._keyfile,
            certfile = self._certfile,
            ca_certs = self._ca_certs,
            cert_reqs = self._cert_reqs,
            server_side = True)
        return client_ssl, addr
