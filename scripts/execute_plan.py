import io
import sys

from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path
from loguru import logger
from PIL import Image


root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer_node import programmer_node  # noqa: E402
from src.models import Plan  # noqa: E402
from src.modules import (  # noqa: E402
    describe_dataframe,
    generate_plan,
)


def main() -> None:
    data_file = "data/sample.csv"
    template_file = "src/prompts/generate_plan.jinja"
    user_request = "scoreを最大化するための広告キャンペーンを検討したい"
    output_dir = "outputs/tmp"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    with open(data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())

    data_info = describe_dataframe(
        file_object=file_object,
        template_file=template_file,
    )
    response = generate_plan(
        data_info=data_info,
        user_request=user_request,
        model="gpt-4o-mini-2024-07-18",
    )

    plan: Plan = response.content

    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(
                programmer_node,
                data_file=data_file,
                user_request=task.hypothesis,
                model="gpt-4o-2024-11-20",
                process_id=f"sample-{idx}",
                idx=idx,
            )
            for idx, task in enumerate(plan.tasks)
        ]
        _results = [future.result() for future in as_completed(futures)]

    saved_files = []
    for _, data_threads in sorted(_results, key=lambda x: x[0]):
        data_thread = data_threads[-1]
        output_file_base = (
            f"{output_dir}/{data_thread.process_id}_"
            f"{data_thread.thread_id}."
        )
        if data_thread.is_completed:
            for i, res in enumerate(data_thread.results):
                if res["type"] == "png":
                    content = res["content"]
                    image_path = f"{output_file_base}_{i}.png"

                    # PIL Imageオブジェクトの場合
                    if hasattr(content, "save"):
                        content.save(image_path)
                    # バイト列の場合
                    elif isinstance(content, bytes):
                        Image.open(BytesIO(content)).save(image_path)
                    # 文字列の場合（base64エンコードされた可能性）
                    elif isinstance(content, str):
                        try:
                            import base64

                            image_bytes = base64.b64decode(content)
                            Image.open(BytesIO(image_bytes)).save(image_path)
                        except Exception as e:
                            logger.warning(
                                f"画像の保存に失敗: {image_path}, {e}"
                            )
                            continue
                    else:
                        logger.warning(
                            f"未対応の画像形式: {type(content)}"
                        )
                        continue

                    saved_files.append(image_path)
                    logger.info(f"画像を保存しました: {image_path}")
                else:
                    text_path = f"{output_file_base}_{i}.txt"
                    with open(text_path, "w", encoding="utf-8") as f:
                        f.write(str(res.get("content", "")))
                    saved_files.append(text_path)
                    logger.info(f"テキストを保存しました: {text_path}")
        else:
            logger.warning(f"{data_thread.user_request=} is not completed.")

    # 保存されたファイルの一覧を表示
    if saved_files:
        print("\n" + "=" * 80)
        print("保存されたファイル:")
        for file_path in saved_files:
            print(f"  - {file_path}")
        print("=" * 80)
    else:
        print("\n保存されたファイルはありません。")


if __name__ == "__main__":
    main()
