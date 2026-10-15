# 学習データがカメラ情報を使えているのかを確認する
# 方法として、２つのエピソードの関節角の情報とカメラ情報を入れ替えて、推論させた結果を比較する
# 入れ替えても結果があまり変わらない = カメラ画像が使えていない
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from huggingface_hub import HfApi
import torch

MODEL = "outputs/models/act_cubecup_soil_wristup_v1_clean_trim"
USER_NAME = HfApi().whoami()["name"]
DATASET = f"{USER_NAME}/so101_cubecup_soil_wristup_v1_clean_trim"

def make_obs(state_frame, image_frame):
    # state_frameの関節角とimage_frameの画像を使った新しいフレームをつくる
    return {
            "observation.state" : state_frame["observation.state"], 
            "observation.images.wrist" : image_frame["observation.images.wrist"], 
            "observation.images.up" : image_frame["observation.images.up"], 
            "task" : state_frame["task"]
            }
def predict_shoulder(pre, post, policy, obs):
    # chunkは(1, 100, 6) -> (batch, step, actions)
    chunk = post(policy.predict_action_chunk(pre(obs)))
    
    # 今回取り出すshoulder panのデータは(0, -1, 0)
    return chunk[0, -1, 0].item()

def main():
    # 1. モデルを読み込んで MPS(Apple SiliconのGPU) に載せる
    policy = ACTPolicy.from_pretrained(MODEL)
    policy.to("mps")
    policy.eval()
    
    # 2. 前処理・後処理を読み込む
    #    このモデルは CUDA で学習されたため、保存された設定では転送先が cuda になっている。
    #    overrides で mps に上書きする
    pre, post = make_pre_post_processors(
        policy.config,
        MODEL,
        preprocessor_overrides={"device_processor": {"device":"mps"}}
    )
    
    # エピソードを読み込む
    swap_episodes = [5, 32] # swapするエピソードを指定
    ds_a = LeRobotDataset(DATASET, episodes=[swap_episodes[0]])
    ds_b = LeRobotDataset(DATASET, episodes=[swap_episodes[1]])
    
    # 特定のフレームだけを取り出して確認する
    check_frames = [0, 40, 80]
    for i in check_frames:
        frame_a = ds_a[i]
        frame_b = ds_b[i]
        
        # 2つのエピソードの関節角と画像を入れ替えたフレームをつくる
        obs_aa = make_obs(frame_a, frame_a)
        obs_ab = make_obs(frame_a, frame_b)
        obs_ba = make_obs(frame_b, frame_a)
        obs_bb = make_obs(frame_b, frame_b)
        
        with torch.inference_mode():
            shoulder_aa = predict_shoulder(pre, post, policy, obs_aa)
            shoulder_ab = predict_shoulder(pre, post, policy, obs_ab)
            shoulder_ba = predict_shoulder(pre, post, policy, obs_ba)
            shoulder_bb = predict_shoulder(pre, post, policy, obs_bb)

        print(f"t={i}, aa={shoulder_aa:.1f}, ab={shoulder_ab:.1f}, bb={shoulder_bb:.1f}, ba={shoulder_ba:.1f}")

if __name__ == "__main__":
    main()