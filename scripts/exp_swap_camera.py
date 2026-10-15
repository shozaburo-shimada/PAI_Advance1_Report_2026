# 俯瞰カメラの影響を調べたい（俯瞰カメラがキューブを見えてないので、精度があがらないのでは？）
#　
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.policies.act.modeling_act import ACTPolicy
from lerobot.policies.factory import make_pre_post_processors
from huggingface_hub import HfApi
import torch
import numpy as np

MODEL = "outputs/models/act_cubecup_soil_wristup_v1_clean_trim"
USER_NAME = HfApi().whoami()["name"]
DATASET = f"{USER_NAME}/so101_cubecup_soil_wristup_v1_clean_trim"
DEGREE_GRIP_CLOSE = 8
DEGREE_GRIP_OPEN = 15
DELTA_FRAME = 15 # 閉じた角度から閉じる直前まで巻き戻すフレーム数 

def make_obs(state_frame, wrist_frame, up_frame):
    # カメラ画像をWrist
    return {
            "observation.state" : state_frame["observation.state"], 
            "observation.images.wrist" : wrist_frame["observation.images.wrist"], 
            "observation.images.up" : up_frame["observation.images.up"], 
            "task" : state_frame["task"]
            }
def predict_shoulder(pre, post, policy, obs):
    # chunkは(1, 100, 6) -> (batch, step, actions)
    chunk = post(policy.predict_action_chunk(pre(obs)))
    
    # 今回取り出すshoulder panのデータは(0, 10, 0)
    # chunkの中で10フレーム先のものを使う
    return chunk[0, 10, 0].item()

def search_grip_frame(dataset):
    # エピソードa, bそれぞれで、つかむ瞬間のフレームを探す
    action_frames = np.array(dataset.hf_dataset["action"])
    flag_opened = False
    for i in range(len(action_frames)):
        # 6番目がgripper
        
        degree_grip = action_frames[i][5]
        if not flag_opened and degree_grip > DEGREE_GRIP_OPEN:
            frame_open = i
            flag_opened = True
        if flag_opened and degree_grip < DEGREE_GRIP_CLOSE:
            frame_close = i
            break
    
    return frame_open, frame_close

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
    
    open_frame_a, close_frame_a = search_grip_frame(ds_a)
    open_frame_b, close_frame_b = search_grip_frame(ds_b) 
    pre_frame_a = close_frame_a - DELTA_FRAME
    pre_frame_b = close_frame_b - DELTA_FRAME
    
    # 特定のフレームだけを取り出して確認する
    frame_a = ds_a[pre_frame_a]
    frame_b = ds_b[pre_frame_b]
    
    # 2つのエピソードのWristとUpの画像を入れ替える
    obs_aaa = make_obs(frame_a, frame_a, frame_a)
    obs_bbb = make_obs(frame_b, frame_b, frame_b)
    obs_aba = make_obs(frame_a, frame_b, frame_a)
    obs_aab = make_obs(frame_a, frame_a, frame_b)
    obs_abb = make_obs(frame_a, frame_b, frame_b)
    
    with torch.inference_mode():
        shoulder_aaa = predict_shoulder(pre, post, policy, obs_aaa)
        shoulder_bbb = predict_shoulder(pre, post, policy, obs_bbb)
        shoulder_aba = predict_shoulder(pre, post, policy, obs_aba)
        shoulder_aab = predict_shoulder(pre, post, policy, obs_aab)
        shoulder_abb = predict_shoulder(pre, post, policy, obs_abb)

    print(f"frame_a={pre_frame_a}, frame_b={pre_frame_b}, aaa={shoulder_aaa:.1f}, bbb={shoulder_bbb:.1f}, aba={shoulder_aba:.1f}, aab={shoulder_aab:.1f}, abb={shoulder_abb:.1f}")

if __name__ == "__main__":
    main()