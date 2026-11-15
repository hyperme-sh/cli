FROM gcr.io/distroless/static-debian12:nonroot@sha256:afa5c872c891853ca7fcf1f12c3edb23f7eeef36189728842dd51042ff57f7ab
COPY bin/hypermesh bin/hm /usr/local/bin/
COPY legal /usr/share/doc/hypermesh-cli/
ARG SOURCE_SHA
LABEL org.opencontainers.image.source="https://github.com/hyperme-sh/hypermesh-cli" \
      org.opencontainers.image.revision="${SOURCE_SHA}"
USER 65532:65532
ENTRYPOINT ["/usr/local/bin/hypermesh"]
CMD ["--help"]
