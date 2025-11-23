import re

from e2b_code_interpreter import Sandbox
from loguru import logger

from src.models import DataThread


def clean_code(code: str) -> str:
    """マークダウンのコードブロック記号を除去"""
    # 先頭と末尾の空白を除去
    code = code.strip()
    
    # マークダウンのコードブロック記号を除去
    # ```python や ```py や ``` で始まる場合
    code = re.sub(r'^```(?:python|py)?\s*\n?', '', code, flags=re.MULTILINE)
    # 末尾の ``` を除去
    code = re.sub(r'\n?```\s*$', '', code, flags=re.MULTILINE)
    
    # 行末に残っている可能性のある """ や ''' を除去
    # ただし、コード内の文字列リテラルは保護
    lines = code.split('\n')
    cleaned_lines = []
    for line in lines:
        # 行末の孤立した """ や ''' を除去
        line = re.sub(r'["\']{3}\s*$', '', line)
        cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    
    return code.strip()


def execute_code(
    sandbox: Sandbox,
    process_id: str,
    thread_id: int,
    code: str,
    user_request: str | None = None,
    timeout: int = 1200,
) -> DataThread:
    # マークダウンのコードブロック記号を除去
    cleaned_code = clean_code(code)
    
    execution = sandbox.run_code(
        cleaned_code,
        timeout=timeout,
    )
    # デバッグ情報を簡潔に出力（警告の詳細は除外）
    logger.debug(
        f"Execution completed: "
        f"results={len(execution.results)}, "
        f"error={execution.error is not None}"
    )
    results = [
        {"type": "png", "content": r.png}
        if r.png
        else {"type": "raw", "content": r.text}
        for r in execution.results
    ]
    return DataThread(
        process_id=process_id,
        thread_id=thread_id,
        user_request=user_request,
        code=cleaned_code,  # クリーンアップされたコードを保存
        error=getattr(execution.error, "traceback", None),
        stderr="".join(execution.logs.stderr).strip(),
        stdout="".join(execution.logs.stdout).strip(),
        results=results,
    )
