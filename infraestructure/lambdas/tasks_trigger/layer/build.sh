#!/bin/bash
set -e

PYTHON_VERSION="3.11"
LAYER_NAME="aie-agents-tasks"

BASE_DIR="$(cd "$(dirname "$0")" && pwd)"
LAYER_DIR="$BASE_DIR/layer"
SITE_PACKAGES="$LAYER_DIR/python/lib/python${PYTHON_VERSION}/site-packages"
OUT_ZIP="$BASE_DIR/${LAYER_NAME}.zip"

command -v docker >/dev/null 2>&1 || { echo "Docker not found"; exit 1; }
[ -f "$BASE_DIR/requirements.txt" ] || { echo "requirements.txt not found"; exit 1; }

rm -rf "$LAYER_DIR" "$OUT_ZIP"
mkdir -p "$SITE_PACKAGES"

echo "📦 Installing dependencies INSIDE AWS Lambda Python ${PYTHON_VERSION}"

docker run --rm \
  --platform linux/amd64 \
  --entrypoint /bin/bash \
  -v "$BASE_DIR":/var/task \
  public.ecr.aws/lambda/python:3.11 \
  -lc "
    python -m pip install --upgrade pip &&
    python -m pip install \
      -r /var/task/requirements.txt \
      -t /var/task/layer/python/lib/python${PYTHON_VERSION}/site-packages &&
    find /var/task/layer -type d -name '__pycache__' -exec rm -rf {} + || true &&
    find /var/task/layer -type d -name 'tests' -exec rm -rf {} + || true
  "

echo "🗜️  Zipping layer → $OUT_ZIP"
cd "$LAYER_DIR"
zip -r "$OUT_ZIP" python \
  -x "*/__pycache__/*" -x "*.pyc" -x "*.pyo"
cd - > /dev/null

rm -rf "$LAYER_DIR"