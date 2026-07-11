FROM kubos/kubos-dev@sha256:cd1a02e19b522d045b17bee6fb67a9f7909bb758eaa97ffd804d151b0e3d21b4

ARG RUST_TOOLCHAIN=1.93.0

ENV CARGO_HOME=/opt/cargo
ENV RUSTUP_HOME=/opt/rustup
ENV PATH=/opt/cargo/bin:${PATH}
ENV DEBIAN_FRONTEND=noninteractive

SHELL ["/bin/bash", "-o", "pipefail", "-c"]

RUN sed -i '/xenial/d' /etc/apt/sources.list && \
    apt-get update && \
    apt-get install --yes --no-install-recommends gcc-8 g++-8 clang llvm libclang-dev && \
    ln -sf /usr/bin/gcc-8 /usr/local/bin/cc && \
    ln -sf /usr/bin/g++-8 /usr/local/bin/c++ && \
    ln -sf /usr/bin/gcc-8 /usr/local/bin/gcc && \
    ln -sf /usr/bin/g++-8 /usr/local/bin/g++ && \
    rm -rf /var/lib/apt/lists/*

RUN curl https://sh.rustup.rs -sSf | \
      sh -s -- -y --default-toolchain "${RUST_TOOLCHAIN}" --profile minimal && \
    rustup target add armv7-unknown-linux-gnueabihf && \
    chmod -R a+rX "${CARGO_HOME}" "${RUSTUP_HOME}"
