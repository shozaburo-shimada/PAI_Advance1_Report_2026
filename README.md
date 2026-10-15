# SO-101でキューブを掴んでカップに入れる

* Macbook AirでSO101を動かした
* ポリシーはMacbookでも動かせる軽量なACT
* 学習データは自分で取得
* 学習はHuggingFaceのJobsを利用
* [https://youtu.be/KGm2WCHIJgg?si=2_7T-GYD86-sA2n2](https://youtu.be/KGm2WCHIJgg?si=2_7T-GYD86-sA2n2)

## PC初期設定

```bash
brew install uv ffmpeg  
git clone <このリポジトリ>
cd <リポジトリ>
uv sync   
cp so101.env.example so101.env 
hf auth login
```

---

## ハードウェアの初期設定

- ロボットアームはSO101
- カメラは、[InnoMaker 1080P USB2.0 UVCカメラ、130°広角レンズ](https://amzn.asia/d/00OG51Xc) x 2台
  - １つはアームの手首に取り付け
  - もうひとつは俯瞰できる位置にセット

### 環境変数（so101.env）の設定

以下のコマンドを使って、so101.envの情報を設定する

```bash
# フォロワー、リーダーアームのUSBポートの特定
lerobot-find-port

# カメラ番号の特定
lerobot-find-cameras opencv
```

ここから先のコマンドは、すべて venv と `so101.env` を読み込んだ状態で実行する。

```bash
source .venv/bin/activate
source so101.env
```

### キャリブレーション

```bash
# フォロワー（robot）
lerobot-calibrate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID

# リーダー（teleop）
lerobot-calibrate \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID
```

### テレオペで動作確認

```bash
lerobot-teleoperate \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID \
  --display_data=true
```

---

## データ収集・確認・削除

### 1. データ収集

初回

- commands/record_new.shで実行可能

```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID \
  --display_data=false \
  --dataset.repo_id=${HF_USER}/<データセット名> \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=40 \
  --dataset.reset_time_s=15 \
  --dataset.single_task="Pick up the cube and place it in the cup" \
  --dataset.push_to_hub=false \
  --dataset.no_stamp=true
```

* `--dataset.num_episodes`：連続で取得するエピソード数
* `--display_data=false`：本来はつけたほうがよいかもしれないが、Macbook Airのリソースを奪われないようにするため
* `--dataset.push_to_hub=false`：Hugging Faceにアップロードしない（手元でデータを確認してから上げるため）
* `--dataset.no_stamp=true`：データセットに勝手にタイムスタンプがつくのでつかないように

2 回目以降（ローカルのデータセットに追加）

- commands/record_rerume.shで実行可能

```bash
lerobot-record \
  --robot.type=so101_follower --robot.port=$FOLLOWER_PORT --robot.id=$FOLLOWER_ID \
  --robot.cameras="{wrist: {type: opencv, index_or_path: $WRIST_CAMERA_INDEX, width: 640, height: 480, fps: 30}, up: {type: opencv, index_or_path: $UP_CAMERA_INDEX, width: 640, height: 480, fps: 30}}" \
  --teleop.type=so101_leader --teleop.port=$LEADER_PORT --teleop.id=$LEADER_ID \
  --display_data=false \
  --dataset.repo_id=${HF_USER}/<データセット名> \
  --dataset.num_episodes=5 \
  --dataset.episode_time_s=40 \
  --dataset.reset_time_s=15 \
  --dataset.single_task="Pick up the cube and place it in the cup" \
  --dataset.push_to_hub=false \
  --dataset.no_stamp=true \
  --dataset.root=$HOME/.cache/huggingface/lerobot/${HF_USER}/<データセット名> \
  --resume=true
```

### 2. データの加工

失敗したデータ（エピソード）の削除

```bash
lerobot-edit-dataset \
  --repo_id=${HF_USER}/<元のデータセット名> \
  --operation.type=delete_episodes \
  --operation.episode_indices="[1]" \
  --new_repo_id=${HF_USER}/<削除後のデータセット名>
```

- `--operation.episode_indices`：削除したいエピソードの番号をしてい

データセット前半は動き出すまでの意味のないデータなので以下のスクリプトでまとめて削除

```bash
python3 scripts/trim_idle_start.py
```

### 3. Hugging Face へのアップロード

```bash
python3 scripts/push_dataset.py
```

---

## 学習の実行と確認

### 1. 学習

本番（50,000 ステップ。2 時間 17 分・約 \$2.3）：

```bash
lerobot-train \
  --dataset.repo_id=${HF_USER}/<学習に使うデータセット名> \
  --policy.type=act \
  --policy.repo_id=${HF_USER}/<モデル名> \
  --steps=50000 \
  --save_freq=10000 \
  --save_checkpoint_to_hub=true \
  --job.target=a10g-small \
  --job.timeout=3h
```

* `--policy.type`：ポリシーの種類。今回はACTで。
* `--save_freq` ：ごとにチェックポイントが作られる。そのチェックポイントでも推論の実行ができる。（学習を回しすぎて過学習になってないかチェックするなど）

### 2. 実行後の確認

学習ステップ数とLossの推移を確認する

```bash
python3 scripts/plot_loss.py
```

## 実機での推論

### 1. 推論前の下準備

**HF Jobs で学習したモデルを使うたびに、毎回この手順が必要。**

HF Jobs のイメージ（`lerobot-gpu:latest`）は PyPI 公開前の開発版で、`config.json` に手元の 0.6.1 が知らない `"dtype": null` を書き出す。そのまま `--policy.path=${HF_USER}/<モデル名>` で使うと `error: The fields dtype are not valid for ACTConfig` で止まる。そのため、モデルを `outputs/models/` にダウンロードし、`dtype` を消してから、手元のフォルダを `--policy.path` に指定する。

モデルのダウンロードとconfig.jsonの修正

```bash
hf download ${HF_USER}/<モデル名> --exclude "checkpoints/*" --local-dir outputs/models/<モデル名>
```

- ``output/models/<モデル名>/config.json`` から dtypeの行を消す

### 2. 推論コマンド（実機での実行）

commands/rollout.shでも実行できる

```bash
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
```

* `--duration` ：実行時間の秒数。`0`（初期値）は無制限。この時間をすぎると実行をやめて初期位置に戻る
* `--policy.n_action_steps` ：アクションチャンクから、実際に利用する使うステップ数。（≠アクションチャンク。アクションチャンクを超えられない）

## データ・モデルの一覧

### データセットの一覧

| 名前                                         | 元   | 中身・条件                                                                                                                                 | Hub                                                                                     |
| -------------------------------------------- | ---- | ------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- |
| `tmp_record_trial1`                        | 撮影 | 試し撮り 2 本                                                                                                                              | なし                                                                                    |
| `tmp_record_trial1_delete_test`            | 上   | 削除の練習（1 本）                                                                                                                         | なし                                                                                    |
| `tmp_record_trial2`                        | 撮影 | 試し撮り 2 本（時間切れで終了）                                                                                                            | なし                                                                                    |
| `so101_cubecup_soil_wristup_v1`            | 撮影 | 50 本（10 本ずつ撮影）。置き場所 5 点（長方形の 4 隅と中央 ＝ v場所番号 1・4・6・8・11）                                                   | なし                                                                                    |
| `so101_cubecup_soil_wristup_v1_clean`      | 上   | エピソード 0（開始姿勢が休止姿勢でない）を削除。49 本                                                                                      | [公開](https://huggingface.co/datasets/zaburou/so101_cubecup_soil_wristup_v1_clean)      |
| `so101_cubecup_soil_wristup_v1_clean_trim` | 上   | 各エピソード先頭の待ち時間を削除。49 本                                                                                                    | [公開](https://huggingface.co/datasets/zaburou/so101_cubecup_soil_wristup_v1_clean_trim) |
| `so101_cubecup_soil_wristup_v2`            | 撮影 | 置き場所 11 点（場所番号 1〜11、v1 の 5 点を含む）に毎回ぴったり置く。1 セッション＝1 点×5 本。ただし、途中での取り直しなどがあり合計60本 | なし                                                                                    |
| `so101_cubecup_soil_wristup_v2_clean`      | 上   | エピソード 0・15・19・26・27を削除。55 本（11 点×5 本）                                                                                   | なし                                                                                    |
| `so101_cubecup_soil_wristup_v2_clean_trim` | 上   | 開始時の待ち時間を削除。55 本                                                                                                              | [公開](https://huggingface.co/datasets/zaburou/so101_cubecup_soil_wristup_v2_clean_trim) |

### モデルの一覧

| 名前                                       | 学習データ           | 学習条件                 | Hub                                                                          |
| ------------------------------------------ | -------------------- | ------------------------ | ---------------------------------------------------------------------------- |
| `tmp_act_v1_clean_2k`                    | `…_v1_clean`      | 2,000 ステップ（試運転） |                                                                              |
| `act_cubecup_soil_wristup_v1_clean`      | `…_v1_clean`      | 50,000 ステップ          | [公開](https://huggingface.co/zaburou/act_cubecup_soil_wristup_v1_clean)      |
| `act_cubecup_soil_wristup_v1_clean_trim` | `…_v1_clean_trim` | 50,000 ステップ          | [公開](https://huggingface.co/zaburou/act_cubecup_soil_wristup_v1_clean_trim) |
| `act_cubecup_soil_wristup_v2_clean_trim` | `…_v2_clean_trim` | 50,000 ステップ          | [公開](https://huggingface.co/zaburou/act_cubecup_soil_wristup_v2_clean_trim) |


## その他

- scripts/exp_swap_state_image.py
  - ２つのエピソードのstate（関節角）とimage（カメラ画像）を入れ替えるスクリプト
- scripts/exp_swap_camera.py
  - ２つのエピソードのwrist image（手首のカメラ画像）とup（俯瞰のカメラ画像）を入れ替えるスクリプト。両方入れ替える（それは上のスクリプト）のではなく、どちらか一方だけ入れ替える。
