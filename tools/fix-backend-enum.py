#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service/src/backend.rs")
t = p.read_text()
old = """pub enum BackendError {
    #[error(\"{0}\")]
    InvalidConfig(String),
    #[error(\"I/O error: {0}\")]
    Io(#[from] std::io::Error),
    #[error(\"invalid backend config: {0}\")]
    InvalidConfig(String),
"""
new = """pub enum BackendError {
    #[error(\"I/O error: {0}\")]
    Io(#[from] std::io::Error),
    #[error(\"invalid backend config: {0}\")]
    InvalidConfig(String),
"""
if old not in t:
    raise SystemExit("enum pattern not found:\n" + t[:500])
p.write_text(t.replace(old, new, 1))
print("fixed BackendError enum")
# verify
t2 = p.read_text()
assert t2.count("InvalidConfig(String)") == 1
print("ok")
