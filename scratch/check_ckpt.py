import torch

ckpt_path = "dataset/models_v2/rnn_ratio_nodetach.pt"
try:
    ckpt = torch.load(ckpt_path, map_location="cpu")
    print("Keys:", list(ckpt.keys()))
    if "history" in ckpt:
        print("History length:", len(ckpt["history"]))
        print("Last epoch in history:", ckpt["history"][-1] if ckpt["history"] else "Empty")
    if "calib_h" in ckpt:
        print("calib_h:", ckpt["calib_h"])
    if "test_metrics" in ckpt:
        print("test_metrics:", ckpt["test_metrics"])
except Exception as e:
    print("Error:", e)
