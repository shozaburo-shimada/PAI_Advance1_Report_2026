# %%
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.constants import DEFAULT_FEATURES
import numpy as np

# %%

# Hugging Face Repo ID
DATASET = "zaburou/so101_cubecup_soil_wristup_v2_clean"
NEW_DATASET = "zaburou/so101_cubecup_soil_wristup_v2_clean_trim"
ANGLE_THRESHOLD = 3
MARGIN_FRAMES = 10

# %%

def main():
    # 丸ごと読みこむとエピソード区切りが分からないので、まずはエピソードの総数を調べる
    all_ds = LeRobotDataset(DATASET)
    total_episodes = all_ds.meta.info.total_episodes
    
    # データセットを作る前の事前準備
    # 既存データセットのfeaturesから、DEFAULT_FEATURESを除く
    # (DEFAULT_FEATURESはLeRobotが自動で付与するため)
    features = {}
    for key, value in all_ds.meta.info.features.items():
        # keyがDEFAULT_FEATURESに含まれていなければ
        if key not in DEFAULT_FEATURES:
            features[key] = value        
    print(features.keys()) 

    # 新しいデータセットをつくる
    new_ds = LeRobotDataset.create(
        repo_id=NEW_DATASET,
        fps=all_ds.meta.info.fps,               #元のデータセットに合わせる
        robot_type=all_ds.meta.info.robot_type, #元のデータセットに合わせる
        features=features,     
        use_videos=True
        )

    # for trial
    for episode in range(total_episodes):
        # 改めてエピソード毎にデータセットを読み込む
        ds = LeRobotDataset(DATASET, episodes=[episode])

        # データセットからアクションだけ取り出して、numpy配列にする
        actions = np.array(ds.hf_dataset["action"])
        # 6軸の各フレームのアクションを初期値と差分を取る
        delt_acts = np.abs(actions - actions[0])
        # 各フレームの中で、6軸の中の最大値を取り出す
        delt_acts_max = delt_acts.max(axis=1)
        # 全フレームの中で最初にtrueになったフレームのインデックスを取り出す
        start_frame = np.argmax(delt_acts_max > ANGLE_THRESHOLD) - MARGIN_FRAMES
        if start_frame < 0: 
            start_frame = 0
        print(episode, len(ds), start_frame)
        

        for i in range (start_frame,len(ds)):
            frame = ds[i]
            new_frame = {}
            for key in features:
                value = frame[key]
                # 書き込むkeyがvideoの場合は変換
                # データセットを読み込むとライブラリが自動で変換しているためそれを元に戻す
                if features[key]["dtype"] == "video":
                    value = value.permute(1,2,0) # 要素の並べ替え(H, W, channel)
                    value = (value * 255).round().byte()
                new_frame[key] = value
        
            new_frame["task"] = frame["task"]
            new_ds.add_frame(new_frame)
        new_ds.save_episode()
        
    new_ds.finalize()
    
if __name__ == "__main__":
    main()
# %%
