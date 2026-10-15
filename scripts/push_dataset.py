
import argparse
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.constants import HF_LEROBOT_HOME
from huggingface_hub import HfApi

def main():
    parser = argparse.ArgumentParser(description="LeRobot データセットを Hugging Face に非公開でアップロードする")
    parser.add_argument("repo_id", help="アップロードするデータセットの repo_id. 例: username/dataset_name, username を省略した場合は、Hugging Face のユーザーネームが自動で付与されます。")  
    args = parser.parse_args()
    
    if "/" not in args.repo_id:
        # repo_idにユーザーネームが含まれていない場合
        # HFのユーザーネームを取得
        user_name = HfApi().whoami()["name"]
        repo_id = f"{user_name}/{args.repo_id}"
    else:
        # repo_idにユーザーネームが含まれている場合
        repo_id = args.repo_id
    

    print("repo id: " + repo_id)

    # ローカルにデータセットがあるか確認
    if not HF_LEROBOT_HOME.joinpath(repo_id).exists():
        print("ローカルにデータがありません") 
        raise SystemExit(1)
    
    # Hugging Faceに既に同じ名前のデータセットが存在するか確認
    if HfApi().repo_exists(repo_id=repo_id, repo_type="dataset"): 
        print("既にHuggingFaceに同じ名前のデータセットが存在します")
        raise SystemExit(1)

    ds = LeRobotDataset(repo_id)

    print("Hugging Faceにアップロードを開始します。")
    ds.push_to_hub(private=True)

    print("アップロードが完了しました。")

if __name__ == "__main__":
    main()