#!/bin/bash
set -eu
grep -E 'error:|Error|undefined|env_mram|fram_mission|BUILD_' \
  /home/logan/radsat-output/build-image.nohup.out | tail -80
