#!/usr/bin/env python3
from pathlib import Path

p = Path("/mnt/c/Users/logan/CubeSAT/Software/services/hardware-services/fram-service/tests/graphql.rs")
t = p.read_text()
old = """            memoryMap {
                capacityBytes
                missionRegionStart
                missionRegionEnd
                freeRegionStart
                freeRegionEnd
                regions { name startOffset endOffset sizeBytes }
"""
new = """            memoryMap {
                capacityBytes
                layoutMagic
                layoutVersion
                missionRegionStart
                missionRegionEnd
                freeRegionStart
                freeRegionEnd
                regions { name startOffset endOffset sizeBytes }
"""
if old not in t:
    raise SystemExit("memoryMap query block missing")
t = t.replace(old, new, 1)
old_assert = """    assert_eq!(map["capacityBytes"], 8192);
    assert_eq!(map["missionRegionStart"], 0);
"""
new_assert = """    assert_eq!(map["capacityBytes"], 8192);
    assert_eq!(map["layoutMagic"], 0x4D_41_52_46i64);
    assert_eq!(map["layoutVersion"], 4);
    assert_eq!(map["missionRegionStart"], 0);
"""
if old_assert not in t:
    raise SystemExit("assert block missing")
t = t.replace(old_assert, new_assert, 1)
p.write_text(t)
print("fram graphql test updated")

