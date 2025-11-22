import sys

from pathlib import Path
from loguru import logger


root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer import programmer_node


def main() -> None:
    _, data_threads = programmer_node(
        data_file="data/sample.csv",
        user_request="スコアの分布を可視化して",
        process_id="programmer"
    )

    logger.info(f"試行回数: {len(data_threads)}")
    for idx, data_thread in enumerate(data_threads):
        print("\n\n")
        print(f"##### {idx} #####")
        print(data_thread.code)
        print("=" * 80)
        print(data_thread.stdout)
        print(data_thread.stderr)
        print("=" * 80)
        print(data_thread.observation)
        print(f"is_completed: {data_thread.is_completed}")


if __name__ == "__main__":
    main()
