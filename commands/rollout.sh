#!/usr/bin/env bash

set -euo pipefail
source "$(dirname "$0")/../so101.env"

lerobot-rollout \
  --strategy.type=base \
  --policy.path=outputs/models/act_cubecup_soil_wristup_v2_clean_trim \
  --policy.device=mps \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --task="Pick up the cube and place it in the cup" \
  --duration=30 \
  --display_data=false \
  --policy.n_action_steps=30