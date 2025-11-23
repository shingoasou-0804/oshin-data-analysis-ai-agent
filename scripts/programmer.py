import sys

from pathlib import Path
from loguru import logger


root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer_node import programmer_node  # noqa: E402


def main() -> None:
    _, data_threads = programmer_node(
        data_file="data/sample.csv",
        user_request="スコアの分布を可視化して",
        process_id="programmer"
    )

    logger.info(f"試行回数: {len(data_threads)}")
    for idx, data_thread in enumerate(data_threads):
        print("\n\n")
        print(f"##### Thread {idx} #####")
        print("コード:")
        print(data_thread.code)
        print("=" * 80)
        if data_thread.stdout:
            print(f"stdout:\n{data_thread.stdout}")
        if data_thread.stderr:
            print(f"stderr:\n{data_thread.stderr}")
        if data_thread.error:
            print(f"error:\n{data_thread.error}")
        print("=" * 80)
        if data_thread.observation:
            print(f"レビュー:\n{data_thread.observation}")
        print(f"is_completed: {data_thread.is_completed}")

        # 保存されたファイルの情報を表示
        if data_thread.pathes:
            print("\n保存されたファイル:")
            for remote_path, local_path in data_thread.pathes.items():
                print(f"  {remote_path} -> {local_path}")

        # 実行結果の画像情報を表示
        if data_thread.results:
            print(f"\n実行結果: {len(data_thread.results)}件")
            for result_idx, result in enumerate(data_thread.results):
                result_type = result.get("type", "unknown")
                if result_type == "png":
                    # 保存された画像のパスを表示
                    filename = (
                        f"thread_{data_thread.thread_id}_"
                        f"result_{result_idx}.png"
                    )
                    image_path = (
                        Path("artifacts") / data_thread.process_id / filename
                    )
                    if image_path.exists():
                        print(
                            f"  画像 {result_idx + 1}: PNG形式 -> {image_path}"
                        )
                    else:
                        print(f"  画像 {result_idx + 1}: PNG形式")
                elif result_type == "raw":
                    content = result.get("content", "")
                    if len(content) > 100:
                        print(f"  テキスト {result_idx + 1}: {content[:100]}...")
                    else:
                        print(f"  テキスト {result_idx + 1}: {content}")


if __name__ == "__main__":
    main()
