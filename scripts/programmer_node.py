import io
from pathlib import Path

from e2b_code_interpreter import Sandbox
from loguru import logger

from src.models import DataThread
from src.modules import (
    describe_dataframe,
    execute_code,
    generate_code,
    generate_review,
    set_dataframe,
)


def programmer_node(
    data_file: str,
    user_request: str,
    process_id: str,
    model: str = "gpt-4o-mini-2024-07-18",
    n_trial: int = 3,
    idx: int = 0,
) -> tuple[int, list[DataThread]]:
    template_file = "src/prompts/describe_dataframe.jinja"
    remote_save_dir = f"outputs/{process_id}"
    with open(data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(
        file_object=file_object,
        template_file=template_file,
    )
    data_threads: list[DataThread] = []
    with Sandbox.create() as sandbox:
        # 出力ディレクトリを作成
        sandbox.run_code(
            f"import os; os.makedirs('{remote_save_dir}', exist_ok=True)"
        )

        with open(data_file, "rb") as fi:
            set_dataframe(
                sandbox=sandbox,
                file_object=fi,
            )
        for thread_id in range(n_trial):
            previous_thread = data_threads[-1] if data_threads else None
            response = generate_code(
                data_info=data_info,
                user_request=user_request,
                previous_thread=previous_thread,
                model=model,
                remote_save_dir=remote_save_dir,
            )
            program = response.content
            logger.info(program.model_dump_json())

            data_thread = execute_code(
                sandbox,
                process_id=process_id,
                thread_id=thread_id,
                code=program.code,
                user_request=user_request,
            )
            if data_thread.stdout:
                logger.info(f"{data_thread.stdout=}")
            if data_thread.stderr:
                logger.warning(f"{data_thread.stderr=}")
            response = generate_review(
                user_request=user_request,
                data_info=data_info,
                data_thread=data_thread,
                model=model,
                remote_save_dir=remote_save_dir,
            )
            review = response.content
            logger.info(review.model_dump_json())
            data_thread.observation = review.observation
            data_thread.is_completed = review.is_completed

            # サンドボックス内の出力ファイルを取得
            try:
                # outputs/{process_id} ディレクトリ内のファイルを取得
                output_files = sandbox.files.list(remote_save_dir)
                saved_files = {}
                for file_info in output_files:
                    # EntryInfoオブジェクトの属性を確認
                    # is_file属性がない場合は、is_dir属性で判定するか、
                    # パスに拡張子があるかで判定
                    is_file = False
                    if hasattr(file_info, "is_file"):
                        is_file = file_info.is_file
                    elif hasattr(file_info, "is_dir"):
                        is_file = not file_info.is_dir
                    else:
                        # パスに拡張子がある場合はファイルとみなす
                        file_path = (
                            getattr(file_info, "path", None)
                            or getattr(file_info, "name", None)
                        )
                        if file_path:
                            is_file = "." in Path(file_path).name

                    if is_file:
                        file_path = (
                            getattr(file_info, "path", None)
                            or getattr(file_info, "name", None)
                        )
                        if not file_path:
                            continue

                        try:
                            # 画像ファイルは実行結果から保存されるため、ここではスキップ
                            file_ext = Path(file_path).suffix.lower()
                            image_exts = [
                                ".png", ".jpg", ".jpeg", ".gif", ".bmp"
                            ]
                            if file_ext in image_exts:
                                logger.debug(
                                    "画像ファイルは実行結果から保存されるため"
                                    f"スキップ: {file_path}"
                                )
                                continue

                            file_content = sandbox.files.read(file_path)
                            # ローカルのartifactsディレクトリに保存
                            artifacts_dir = Path("artifacts") / process_id
                            artifacts_dir.mkdir(parents=True, exist_ok=True)
                            local_path = artifacts_dir / Path(file_path).name

                            if isinstance(file_content, bytes):
                                local_path.write_bytes(file_content)
                            else:
                                local_path.write_text(
                                    str(file_content), encoding="utf-8"
                                )

                            saved_files[file_path] = str(local_path)
                            logger.info(f"保存しました: {local_path}")
                        except Exception as e:
                            logger.warning(f"ファイル取得失敗 {file_path}: {e}")

                data_thread.pathes = saved_files
            except Exception as e:
                logger.warning(f"出力ディレクトリの取得に失敗: {e}")

            # 実行結果の画像を保存
            if data_thread.results:
                artifacts_dir = Path("artifacts") / process_id
                artifacts_dir.mkdir(parents=True, exist_ok=True)
                for result_idx, result in enumerate(data_thread.results):
                    if result.get("type") == "png" and result.get("content"):
                        image_path = (
                            artifacts_dir
                            / f"thread_{thread_id}_result_{result_idx}.png"
                        )
                        content = result["content"]
                        # PIL Imageオブジェクトの場合
                        if hasattr(content, "save"):
                            content.save(image_path)
                        # バイト列の場合
                        elif isinstance(content, bytes):
                            image_path.write_bytes(content)
                        # 文字列の場合（base64エンコードされた可能性）
                        elif isinstance(content, str):
                            try:
                                import base64

                                # base64デコードを試みる
                                image_bytes = base64.b64decode(content)
                                image_path.write_bytes(image_bytes)
                            except Exception:
                                # base64でない場合は、そのままテキストとして保存
                                logger.warning(
                                    f"画像の保存に失敗（文字列形式）: {image_path}"
                                )
                        else:
                            logger.warning(
                                f"未対応の画像形式: {type(content)}"
                            )
                        logger.info(f"画像を保存しました: {image_path}")

            data_threads.append(data_thread)
            if data_thread.is_completed:
                logger.success(f"{user_request=}")
                logger.success(f"{program.code=}")
                logger.success(f"{review.observation=}")
                break
    return idx, data_threads
