import argparse
import matplotlib.pyplot as plt
from pathlib import Path

LOSS_STEP = 200

def load_losses(path):
    with open(path) as f:
        losses = []
        steps = [] 
        #ファイルから1行ずつ取り出す    
        for line in f:
            #lineをスペース毎に区切って分解 
            for word in line.split(): 
                # "loss:"という文字列がある要素だけ取り出す
                if word.startswith("loss:"):
                    loss = float(word.split(":")[1])
                    #print(loss)
                    losses.append(loss)
                    steps.append(LOSS_STEP * len(losses))
    
    return steps, losses

def main():
    parser = argparse.ArgumentParser(description="Hugging Face上での学習のLossをプロットする")
    parser.add_argument("files", nargs="+", help="ログファイルの場所を指定 例:outputs/logs/xxx.log")  
    args = parser.parse_args()
    
    # 複数のファイルを指定されたら1ファイルずつ処理
    for path in args.files:
        steps, losses = load_losses(path)
        label = Path(path).stem
        plt.plot(steps, losses, label=label)
    
    for ckpt in [10000, 20000, 30000, 40000, 50000]:
        plt.axvline(x=ckpt, linestyle="--", color="gray")
    plt.yscale("log")
    plt.xlabel("step")
    plt.ylabel("Loss")
    plt.legend()
    plt.savefig("outputs/loss.png")


if __name__ == "__main__":
    main()