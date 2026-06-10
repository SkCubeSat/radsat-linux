# RadSat self-hosted build runner

The workflow builds inside a pinned Docker image. The host only needs:

- A GitHub Actions runner with the `self-hosted`, `linux`, and `x64` labels
- Docker access for the runner account
- Git, curl, tar, sha256sum, and Python 3

The derived image upgrades the legacy Kubos image from GCC 7 to GCC 8.4.
Buildroot 2025 requires host GCC 8 or newer before it enables ccache.

Reusable build data is stored under `~/.cache/radsat-linux`:

- `archives`: Buildroot release archives
- `buildroot-dl`: downloaded package sources
- `buildroot-ccache`: C and C++ compiler cache
- `cargo`: Cargo registry and Git data
- `cargo-target`: compiled Rust dependencies and applications

Buildroot output is intentionally recreated for every workflow run. This
avoids stale images while retaining the expensive download and compiler
caches.

The pinned builder image is built from `Dockerfile` and remains in the local
Docker image cache. Rebuilding it is quick when the Dockerfile has not
changed.

The old Vagrant VM is not used by this workflow. Shut it down while CI is
running to make its reserved memory and CPU time available to Buildroot:

```bash
cd ~/Documents/kubos-SDK
vagrant halt
```

To clear reusable build data:

```bash
rm -rf ~/.cache/radsat-linux
```

The manual workflow form also has a `reset_build_cache` checkbox. Use it after
changing the Buildroot compiler or toolchain configuration.
