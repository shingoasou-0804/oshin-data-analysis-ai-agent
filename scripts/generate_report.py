import argparse
import io
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))


from scripts.programmer_node import programmer_node
from src.models import Plan
from src.modules import (
    describe_dataframe,
    generate_plan,
    generate_report,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_file", type=str, default="data/sample.csv")
    parser.add_argument("--model", type=str, default="gpt-4o-mini-2024-07-18")
    parser.add_argument("--process_id", type=str, default="sample")
    parser.add_argument(
        "--user_request",
        type=str,
        default="scoreを最大化するための広告キャンペーンを検討したい"),
    args = parser.parse_args()

    output_dir = Path("artifacts") / "report"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 計画生成
    with open(args.data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(file_object=file_object)
    response = generate_plan(
        data_info=data_info,
        user_request=args.user_request,
        model=args.model,
    )
    plan: Plan = response.content

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                programmer_node,
                data_file=args.data_file,
                user_request=task.hypothesis,
                model=args.model,
                process_id=f"sample-{idx}",
                idx=idx,
            )
            for idx, task in enumerate(plan.tasks)
        ]
        _results = [future.result() for future in as_completed(futures)]

    process_data_threads = []
    for _, data_threads in sorted(_results, key=lambda x: x[0]):
        process_data_threads.append(data_threads[-1])

    response = generate_report(
        data_info=data_info,
        user_request=args.user_request,
        process_data_threads=process_data_threads,
        model=args.model,
        output_dir=str(output_dir),
    )


if __name__ == "__main__":
    main()
