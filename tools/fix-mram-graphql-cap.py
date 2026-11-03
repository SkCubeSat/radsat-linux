#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/mram-service/tests/graphql.rs")
t = p.read_text()
t = t.replace(
    'assert_eq!(data["storage"]["capacityBytes"], 524_288);',
    'assert_eq!(data["storage"]["capacityBytes"], 514_048);',
)
if "env_offset = 514048" not in t:
    t = t.replace(
        "image_capacity_bytes = 524288\n",
        "image_capacity_bytes = 524288\nenv_offset = 514048\nenv_size = 10240\n",
    )
p.write_text(t)
print("fixed capacity assert")
print("has 514_048", "514_048" in t)

# verify sync script
s = Path("/mnt/c/Users/logan/CubeSAT/radsat-linux/tools/sync-and-build-image.sh").read_text()
for needle in [
    "0006-bbb-env-on-spi-mram.patch",
    "0007-bbb-fram-mission-policy.patch",
    "S79mram-env-sync",
    "fram-get",
    "kubos-mram-dirclean",
    'FORCE_KUBOS:-1',
]:
    print(needle, needle in s)
