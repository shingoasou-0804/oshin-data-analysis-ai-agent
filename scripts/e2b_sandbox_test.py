from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from loguru import logger


def main() -> None:
    load_dotenv()
    with Sandbox.create() as sandbox:
        execution = sandbox.run_code("print('Hello, World!')")

        # stdoutとlogsを取得
        stdout = execution.text or ""
        logger.info(f"Stdout: {stdout}")

        # Logsオブジェクトを文字列に変換
        if execution.logs:
            has_stdout = (
                hasattr(execution.logs, 'stdout') and execution.logs.stdout
            )
            if has_stdout:
                logs_str = "\n".join(
                    str(line) for line in execution.logs.stdout
                )
                logger.info(f"Logs: {logs_str}")
            else:
                logger.info(f"Logs: {str(execution.logs)}")


if __name__ == "__main__":
    main()
