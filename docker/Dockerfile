# Official xcube server image for personal xcube pods (M2, UR-35).
# Pinned to the same xcube version as the local development environment and built natively
# (multi-arch micromamba base), so Apple Silicon does not need amd64 emulation.
FROM mambaorg/micromamba:2.0.5-debian12-slim

ARG XCUBE_VERSION=1.13.1
RUN micromamba install -y -n base -c conda-forge "python=3.12" "xcube=${XCUBE_VERSION}" \
 && micromamba clean --all --yes

ENV MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /home/mambauser
EXPOSE 8080
# The micromamba entrypoint activates the base env; pods pass `xcube serve ...` as arguments.
CMD ["xcube", "serve", "--help"]
