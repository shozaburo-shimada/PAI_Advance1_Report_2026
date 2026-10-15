#!/usr/bin/env bash

# 過去のデータセットに追加で記録する場合（２回目以降の記録）

set -euo pipefail
source "$(dirname "$0")/../so101.env"

NUM_EPISODES="${1:?エピソード数を指定してください}"     # 1番目の引数。省略したら 5

lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID \
  --display_data=false \
  --dataset.repo_id=${HF_USER}/so101_cubecup_soil_wristup_v2 \
  --dataset.num_episodes=${NUM_EPISODES} \
  --dataset.episode_time_s=40 \
  --dataset.reset_time_s=10 \
  --dataset.single_task="Pick up the cube and place it in the cup" \
  --dataset.push_to_hub=false \
  --dataset.no_stamp=true \
  --dataset.root=$HOME/.cache/huggingface/lerobot/${HF_USER}/so101_cubecup_soil_wristup_v2 \
  --resume=true

