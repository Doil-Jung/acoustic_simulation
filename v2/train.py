"""
학습 스크립트 v1 — 베이스라인 CNN (§8 1칸).
CLI:  python v2/train.py --data dataset/v2 --mode ratio --epochs 30 --name base_ratio
앱(3번 탭)에서는 train()을 직접 호출(progress_cb로 진행 표시).

체크포인트(dataset/models_v2/{name}.pt):
  model_state / arch{n_bins,d} / aug{mode,crop} / split{seed,test_idx}
  / history / 물리상수 스냅샷(정규화 기준 재현용)
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from v2 import config
from v2.data import loader
from v2.models.baseline import MaskedSetBaseline, masked_loss, mae_mm


def build_datasets(data_dir, aug_cfg, max_samples, split_seed=42):
    import torch
    from torch.utils.data import Dataset

    store = loader.ChunkStore(data_dir, max_samples=max_samples)
    n = len(store)
    perm = np.random.default_rng(split_seed).permutation(n)
    n_tr, n_va = int(n * 0.8), int(n * 0.1)
    idx = {"train": perm[:n_tr], "val": perm[n_tr:n_tr + n_va], "test": perm[n_tr + n_va:]}

    base_rng = np.random.default_rng(0)
    signatures = loader.load_or_synth_signatures(aug_cfg, base_rng)

    class DS(Dataset):
        def __init__(self, indices, deterministic):
            self.indices = indices
            self.det = deterministic

        def __len__(self):
            return len(self.indices)

        def __getitem__(self, k):
            i = int(self.indices[k])
            rng = np.random.default_rng((1234, i)) if self.det else np.random.default_rng()
            spec, v, H, lab, lm = store.get_raw(i)
            spec, v = loader.augment_sequence(spec, v, aug_cfg, rng, signatures)
            h_n, r_n = loader.normalize_labels(H, lab)
            return spec, v, h_n, r_n, lm

    def collate(batch):
        arrs = loader.collate_numpy(batch, aug_cfg.n_bins)
        return tuple(torch.from_numpy(a) for a in arrs)

    return store, idx, DS(idx["train"], False), DS(idx["val"], True), DS(idx["test"], True), collate


def train(data_dir="dataset/v2", mode="ratio", crop=config.CROP_DEFAULT,
          epochs=30, batch=64, lr=1e-3, max_samples=None, device=None,
          name="base_ratio", h_weight=3.0, num_workers=0, progress_cb=None):
    import torch
    from torch.utils.data import DataLoader

    device = device or ("cuda" if torch.cuda.is_available() else "cpu")
    aug_cfg = loader.AugmentConfig(mode=mode, crop_hz=crop)
    store, idx, ds_tr, ds_va, ds_te, collate = build_datasets(data_dir, aug_cfg, max_samples)
    print(f"[data] {len(store)} samples | bins={aug_cfg.n_bins} | mode={mode} | device={device}")

    dl_tr = DataLoader(ds_tr, batch_size=batch, shuffle=True, collate_fn=collate, num_workers=num_workers)
    dl_va = DataLoader(ds_va, batch_size=batch, shuffle=False, collate_fn=collate, num_workers=num_workers)

    model = MaskedSetBaseline(aug_cfg.n_bins).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=lr)
    history, best_val = [], float("inf")
    os.makedirs("dataset/models_v2", exist_ok=True)
    ckpt_path = f"dataset/models_v2/{name}.pt"

    def run_epoch(dl, train_mode):
        model.train(train_mode)
        tot, n_seen, h_mms, r_mms = 0.0, 0, [], []
        with torch.set_grad_enabled(train_mode):
            for X, V, sm, yh, yr, lm in dl:
                X, V, sm = X.to(device), V.to(device), sm.to(device)
                yh, yr, lm = yh.to(device), yr.to(device), lm.to(device)
                ph, pr = model(X, V, sm)
                loss, _, _ = masked_loss(ph, pr, yh, yr, lm, h_weight)
                if train_mode:
                    opt.zero_grad(); loss.backward(); opt.step()
                bs = X.size(0)
                tot += loss.item() * bs; n_seen += bs
                hm, rm = mae_mm(ph, pr, yh, yr, lm)
                h_mms.append(hm * bs); r_mms.append(rm * bs)
        return tot / n_seen, sum(h_mms) / n_seen, sum(r_mms) / n_seen

    t0 = time.time()
    for ep in range(1, epochs + 1):
        tr_loss, _, _ = run_epoch(dl_tr, True)
        va_loss, va_h, va_r = run_epoch(dl_va, False)
        history.append((ep, tr_loss, va_loss, va_h, va_r))
        msg = (f"[{ep:3d}/{epochs}] train {tr_loss:.5f} | val {va_loss:.5f} "
               f"| H_MAE {va_h:6.1f}mm | r_MAE {va_r:5.2f}mm | {time.time()-t0:5.0f}s")
        print(msg, flush=True)
        if progress_cb:
            progress_cb(ep, epochs, msg, history)
        if va_loss < best_val:
            best_val = va_loss
            import torch as _t
            _t.save({
                "model_state": model.state_dict(),
                "arch": {"n_bins": aug_cfg.n_bins, "n_slots": config.N_SLOTS},
                "aug": {"mode": mode, "crop_hz": crop},
                "split": {"seed": 42, "test_idx": idx["test"].tolist(),
                          "max_samples": max_samples, "data_dir": data_dir},
                "norms": {"H_MIN": config.H_MIN, "H_MAX": config.H_MAX,
                          "R_MIN": config.R_MIN, "R_MAX": config.R_MAX,
                          "V_NORM": config.V_NORM},
                "history": history,
            }, ckpt_path)

    # 미확인 테스트셋 최종 평가 (베스트 가중치)
    ck = torch.load(ckpt_path, map_location=device, weights_only=False)
    model.load_state_dict(ck["model_state"])
    dl_te = DataLoader(ds_te, batch_size=batch, shuffle=False, collate_fn=collate)
    te_loss, te_h, te_r = run_epoch(dl_te, False)
    print(f"[TEST] loss {te_loss:.5f} | H_MAE {te_h:.1f}mm | r_MAE {te_r:.2f}mm")
    ck["test_metrics"] = {"loss": te_loss, "H_MAE_mm": te_h, "r_MAE_mm": te_r}
    torch.save(ck, ckpt_path)
    print(f"[SAVED] {ckpt_path}")
    return ckpt_path, history


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="dataset/v2")
    ap.add_argument("--mode", choices=["ratio", "absolute"], default="ratio")
    ap.add_argument("--crop", type=float, default=config.CROP_DEFAULT)
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--batch", type=int, default=64)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--device", default=None)
    ap.add_argument("--name", default="base_ratio")
    ap.add_argument("--h_weight", type=float, default=3.0)
    ap.add_argument("--workers", type=int, default=0)
    ap.add_argument("--smoke", action="store_true", help="초소형 동작 확인")
    a = ap.parse_args()
    if a.smoke:
        a.samples, a.epochs, a.batch = 48, 2, 8
    train(a.data, a.mode, a.crop, a.epochs, a.batch, a.lr, a.samples,
          a.device, a.name, a.h_weight, a.workers)


if __name__ == "__main__":
    main()
