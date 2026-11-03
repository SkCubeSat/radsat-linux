#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/fram-service/src/subsystem.rs")
t = p.read_text()
t2 = t.replace('"/dev/i2c-1"', '"/dev/i2c-2"')
p.write_text(t2)
print("fixed i2c default to i2c-2")
