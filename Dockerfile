FROM python:3.8-alpine as base
FROM base as builder

COPY requirements.txt /app/
COPY setup.py /app/
COPY README.md /app/
COPY proxy/ /app/proxy/
WORKDIR /app
RUN pip install --upgrade pip && \
    pip install --prefix=/deps .

FROM base

LABEL com.abhinavsingh.name="abhinavsingh/proxy.py" \
      com.abhinavsingh.description="⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on \
        Network monitoring, controls & Application development, testing, debugging." \
      com.abhinavsingh.url="https://github.com/abhinavsingh/proxy.py" \
      com.abhinavsingh.vcs-url="https://github.com/abhinavsingh/proxy.py" \
      com.abhinavsingh.docker.cmd="docker run -it --rm -p 8899:8899 abhinavsingh/proxy.py"

COPY --from=builder /deps /usr/local

# Install openssl to enable TLS interception within container
RUN apk update && apk add openssl

EXPOSE 8899/tcp

RUN mkdir -p /srv/proxy
CMD [ "proxy", \
	"--hostname=0.0.0.0", \
	"--plugins=proxy.plugin.CacheResponsesPlugin,proxy.plugin.RedirectMapPlugin", \
	"--ca-key-file=/srv/proxy/ca-key.pem", \
	"--ca-cert-file=/srv/proxy/ca-cert.pem", \
	"--ca-signing-key-file=/srv/proxy/ca-signing-key.pem", \
	"--ca-file=/srv/proxy/ca-bundle.pem", \
	"--log-level=info", \
	"--cache-dir=/srv/proxy/cache", \
        "--ca-cert-dir=/srv/proxy/mycerts" \
]

