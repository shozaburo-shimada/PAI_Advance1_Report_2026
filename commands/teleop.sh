#!/usr/bin/env bash

set -euo pipefail
source "$(dirname "$0")/../so101.env"

lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID \
  --display_data=true # rerun