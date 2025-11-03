#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from e2b_code_interpreter import Sandbox

ARTIFACTS = Path("artifacts")
REMOTE_PNG = "/workspace/output.png"
REMOTE_TXT = "/workspace/summary.txt"


def ts() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def save_text(name: str, content: str):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / name).write_text(content or "", encoding="utf-8")


def save_bin(name: str, blob: bytes):
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / name).write_bytes(blob)


def main():
    console = Console()
    console.rule("[bold]E2B: 計算+グラフ")

    if not os.getenv("E2B_API_KEY"):
        console.print("[red]E2B_API_KEY が未設定です (.env を確認)[/]")
        raise SystemExit(1)

    with Sandbox.create() as sbx:
        # 作業ディレクトリ & 依存
        sbx.run_code("import os; os.makedirs('/workspace', exist_ok=True)")
        install_cmd = (
            "import subprocess; "
            "subprocess.run(['pip','install','--quiet',"
            "'numpy','pandas','matplotlib'], check=False)"
        )
        sbx.run_code(install_cmd)

        # ---- サンドボックスで実行するコード（stdoutを必ず出す）----
        code = r"""
import os, json, traceback
# バックエンド固定（ヘッドレスでも描画OK）
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, pandas as pd

print("== STDOUT_START ==")

try:
    print("[info] working dir:", os.getcwd())
    # 合成データ: y ≈ 2x + noise
    x = np.arange(1, 51)
    rng = np.random.default_rng(42)
    y = 2 * x + rng.normal(0, 5, size=len(x))
    df = pd.DataFrame({"x": x, "y": y})

    summary = {
        "count": int(len(df)),
        "x_sum": int(df["x"].sum()),
        "y_sum": float(df["y"].sum()),
        "y_mean": float(df["y"].mean()),
        "y_std": float(df["y"].std(ddof=1)),
        "y_min": float(df["y"].min()),
        "y_max": float(df["y"].max()),
    }
    print("[info] summary:", json.dumps(summary, ensure_ascii=False))

    # グラフ
    plt.figure(figsize=(7,3))
    plt.plot(df["x"], df["y"])
    plt.title("Simple Calc & Plot (y ≈ 2x + noise)")
    plt.xlabel("x"); plt.ylabel("y"); plt.tight_layout()
    out_png = "/workspace/output.png"
    plt.savefig(out_png, dpi=160)
    print("[info] saved png:", out_png, "exists?", os.path.exists(out_png))

    # summary.txt も保存
    out_txt = "/workspace/summary.txt"
    with open(out_txt, "w", encoding="utf-8") as f:
        for k, v in summary.items():
            f.write(f"{k}: {v}\n")
    print("[info] saved txt:", out_txt, "exists?", os.path.exists(out_txt))

    # 最後に JSON を必ず print
    print(json.dumps({"ok": True, "summary": summary}, ensure_ascii=False))

except Exception as e:
    print("[error] exception occurred:", repr(e))
    traceback.print_exc()
    print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))

print("== STDOUT_END ==")
"""
        res = sbx.run_code(code)

        # stdout/logs を保存
        stdout = res.text or ""

        # Logsオブジェクトを文字列に変換
        logs_str = ""
        if res.logs:
            if hasattr(res.logs, 'stdout') and res.logs.stdout:
                # Logsオブジェクトのstdoutを結合
                logs_str = "\n".join(
                    str(line) for line in res.logs.stdout
                )
                has_stderr = (
                    hasattr(res.logs, 'stderr') and res.logs.stderr
                )
                if has_stderr:
                    stderr_str = "\n".join(
                        str(line) for line in res.logs.stderr
                    )
                    if stderr_str:
                        logs_str += "\n" + stderr_str
            else:
                # フォールバック: 文字列として扱う
                logs_str = str(res.logs)

        save_text(f"{ts()}-stdout.txt", stdout)
        save_text(f"{ts()}-logs.txt", logs_str)
        stdout_panel = Panel(
            stdout or "(no stdout)", title="Sandbox stdout", expand=False
        )
        console.print(stdout_panel)
        if logs_str:
            logs_display = logs_str[:1500] + (
                " …" if len(logs_str) > 1500 else ""
            )
            console.print(
                Panel(logs_display, title="Sandbox logs", expand=False)
            )

        # 画像と要約テキストを artifacts/ に保存
        try:
            png_data = sbx.files.read(REMOTE_PNG)
            # 文字列の場合はエンコードしてバイト列に変換
            if isinstance(png_data, str):
                png_bytes = png_data.encode('utf-8')
            elif isinstance(png_data, bytes):
                png_bytes = png_data
            else:
                # memoryviewなどの場合
                png_bytes = bytes(png_data)

            png_name = f"{ts()}-output.png"
            save_bin(png_name, png_bytes)
            console.print(f"[green]Saved:[/] artifacts/{png_name}")
        except Exception as e:
            console.print(f"[yellow]PNG 取得失敗:[/] {e}")

        try:
            txt_data = sbx.files.read(REMOTE_TXT)
            # 既に文字列の場合はそのまま、バイト列の場合はデコード
            if isinstance(txt_data, bytes):
                summary_txt = txt_data.decode("utf-8")
            else:
                summary_txt = str(txt_data)

            txt_name = f"{ts()}-summary.txt"
            save_text(txt_name, summary_txt)
            console.print(f"[green]Saved:[/] artifacts/{txt_name}")
        except Exception as e:
            console.print(f"[yellow]summary.txt 取得失敗:[/] {e}")

    console.rule("[bold green]完了")


if __name__ == "__main__":
    main()
