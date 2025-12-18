#!/bin/bash
set -e

TENANT_ID="${1:?Usage: $0 <tenant_id>}"

if [ -z "$TENANT_ID" ] ; then
  echo "Usage: ./zip.sh <tenant_id>"
  exit 1
fi

LAMBDA_NAME="aie_agents_tasks_trigger"
LAMBDA_DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$LAMBDA_DIR/$LAMBDA_NAME.zip"

CONFIG_FILE="../../../config/tenants/${TENANT_ID}.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE"
  exit 1
fi

mkdir -p "$LAMBDA_DIR/agents" "$LAMBDA_DIR/core" "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/models" "$LAMBDA_DIR/services"

cp "$CONFIG_FILE" "$LAMBDA_DIR/tenant_config.yaml"

cp -r ../../../agents/* "$LAMBDA_DIR/agents/"
cp -r ../../../core/* "$LAMBDA_DIR/core/"
cp -r ../../../integrations/* "$LAMBDA_DIR/integrations/"
cp -r ../../../models/* "$LAMBDA_DIR/models/"
cp -r ../../../services/* "$LAMBDA_DIR/services/"

cd "$LAMBDA_DIR"
zip -r $LAMBDA_NAME.zip \
  lambda_function.py tenant_config.yaml agents core integrations models services yaml _yaml \
  -x "*/__pycache__/*" -x "*.pyc" -x "*.pyo"
cd - > /dev/null

rm -rf "$LAMBDA_DIR/agents" "$LAMBDA_DIR/core" "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/models" "$LAMBDA_DIR/services" "$LAMBDA_DIR/tenant_config.yaml"

rm -rf "$LAMBDA_DIR/yaml" "$LAMBDA_DIR/_yaml" "$LAMBDA_DIR/PyYAML-"* "$LAMBDA_DIR/pyyaml-"* "$LAMBDA_DIR/yaml-"* "$LAMBDA_DIR/*.dist-info"