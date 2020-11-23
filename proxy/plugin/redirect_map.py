# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.
"""
from typing import Optional

from ..common.utils import build_http_response
from ..http.parser import HttpParser
from ..http.codes import httpStatusCodes
from ..http.proxy import HttpProxyBasePlugin
from ..http.exception import HttpRequestRejected

import logging

logger = logging.getLogger(__name__)

class RedirectMapPlugin(HttpProxyBasePlugin):
    """Reroutes requests to a different host (including https)"""

    def before_upstream_connection(
            self, request: HttpParser) -> Optional[HttpParser]:
        request = self.rewrite_request(request)
        return request

    def handle_client_request(
            self, request: HttpParser) -> Optional[HttpParser]:
        request = self.rewrite_request(request)
        return request


    host_map = {
        b'pypi.org' :            b'pypi.minibuild',
        b'rubygems.org' :        b'rubygems.minibuild',
        b'api.rubygems.org' :    b'rubygems.minibuild',
        b'index.rubygems.org' :  b'rubygems.minibuild',
        b'gem.mutant.dev' :      b'rubygems.minibuild',
    }

    allow_map = {
        b'github.com' :         True,
        b'pypi.minibuild' :     True,
        b'rubygems.minibuild' : True,
    }

    def rewrite_request(
            self, request: HttpParser) -> Optional[HttpParser]:
        if request.method != b'CONNECT':
                logger.info("Not rewriting request %s %s" % (request.method, request.url))
                return request

        host = request.host
        if host is None and b'host' in request.headers:
                host = request.header(b'host')

        if host is None:
                raise HttpRequestRejected(
                    status_code = httpStatusCodes.NOT_FOUND,
                    headers={b'Connection': b'close'},
                    reason=b'Blocked',
                )

        mapped = self.host_map.get(host)
        if mapped is not None:
                import urllib

                logger.info("Remapping request for host %s to %s" % (host, mapped))
                request.set_url(mapped + request.url.path)

                # Stick the original host name in the Host: header so that the server
                # can match for that.
                if request.has_header(b'Host'):
                    request.del_header(b'Host')
                request.add_header(b'Host', host)

                # Ensure that we use the original hostname when creating the MITM
                # certificate
                request.orig_request_host = host
        elif not self.allow_map.get(host):
                logger.info("Rejecting connection to host %s" % (host))
                raise HttpRequestRejected(
                    status_code=httpStatusCodes.I_AM_A_TEAPOT, reason=b'I\'m a tea pot',
                    headers={
                        b'Connection': b'close',
                    }
                )

        return request

    def handle_upstream_chunk(self, chunk: memoryview) -> memoryview:
        return chunk

    def on_upstream_connection_close(self) -> None:
        pass
