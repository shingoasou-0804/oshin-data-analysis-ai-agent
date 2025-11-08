.PHONY: help install install-dev format lint type-check test clean docker-build docker-up docker-down docker-logs run shell

# サービス名
SERVICE = agent

# デフォルトターゲット
help:
	@echo "利用可能なコマンド:"
	@echo "  make install       - 依存関係をインストール（コンテナ内）"
	@echo "  make install-dev   - 開発用依存関係を含めてインストール（コンテナ内）"
	@echo "  make format        - コードをフォーマット（コンテナ内）"
	@echo "  make lint          - リンターを実行（コンテナ内）"
	@echo "  make lint-fix      - リンター自動修正（コンテナ内）"
	@echo "  make type-check    - 型チェックを実行（コンテナ内）"
	@echo "  make test          - テストを実行（コンテナ内）"
	@echo "  make check         - フォーマット、リンター、型チェックを実行（コンテナ内）"
	@echo "  make clean         - キャッシュと一時ファイルを削除（コンテナ内）"
	@echo "  make docker-build  - Dockerイメージをビルド"
	@echo "  make docker-up     - Docker Composeでコンテナを起動"
	@echo "  make docker-down   - Docker Composeでコンテナを停止"
	@echo "  make docker-logs   - Docker Composeのログを表示"
	@echo "  make run           - アプリケーションを実行（コンテナ内）"
	@echo "  make shell         - コンテナ内のシェルに接続"

# 依存関係のインストール
install:
	docker compose run --rm $(SERVICE) uv sync

# 開発用依存関係を含めてインストール
install-dev:
	docker compose run --rm $(SERVICE) uv sync --extra dev

# コードフォーマット
format:
	docker compose run --rm $(SERVICE) uv run ruff format .

# リンター実行
lint:
	docker compose run --rm $(SERVICE) uv run ruff check .

# リンター自動修正
lint-fix:
	docker compose run --rm $(SERVICE) uv run ruff check --fix .

# 型チェック
type-check:
	docker compose run --rm $(SERVICE) uv run mypy src

# テスト実行
test:
	docker compose run --rm $(SERVICE) uv run pytest

# フォーマット、リンター、型チェックをすべて実行
check: format lint type-check
	@echo "すべてのチェックが完了しました"

# クリーンアップ
clean:
	docker compose run --rm $(SERVICE) sh -c "find . -type d -name '__pycache__' -exec rm -r {} + 2>/dev/null || true; \
		find . -type f -name '*.pyc' -delete; \
		find . -type f -name '*.pyo' -delete; \
		find . -type d -name '*.egg-info' -exec rm -r {} + 2>/dev/null || true; \
		find . -type d -name '.mypy_cache' -exec rm -r {} + 2>/dev/null || true; \
		find . -type d -name '.ruff_cache' -exec rm -r {} + 2>/dev/null || true; \
		find . -type d -name '.pytest_cache' -exec rm -r {} + 2>/dev/null || true"

# Dockerイメージをビルド
docker-build:
	docker compose build

# Docker Composeでコンテナを起動
docker-up:
	docker compose up -d

# Docker Composeでコンテナを停止
docker-down:
	docker compose down

# Docker Composeのログを表示
docker-logs:
	docker compose logs -f

# アプリケーションを実行
run:
	docker compose run --rm $(SERVICE) uv run python main.py

# コンテナ内のシェルに接続
shell:
	docker compose exec $(SERVICE) /bin/bash || docker compose run --rm $(SERVICE) /bin/bash

