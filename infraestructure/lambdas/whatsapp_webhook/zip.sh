#!/bin/bash
set -e

TENANT_ID="${1:?Usage: $0 <tenant_id>}"

if [ -z "$TENANT_ID" ] ; then
  echo "Usage: ./zip.sh <tenant_id>"
  exit 1
fi

LAMBDA_NAME="aie_agents_whatsapp_webhook"
LAMBDA_DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$LAMBDA_DIR/$LAMBDA_NAME.zip"

CONFIG_FILE="../../../config/tenants/${TENANT_ID}.yaml"
if [ ! -f "$CONFIG_FILE" ]; then
  echo "Config file not found: $CONFIG_FILE"
  exit 1
fi

mkdir -p "$LAMBDA_DIR/core" "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/services" "$LAMBDA_DIR/models"

cp "$CONFIG_FILE" "$LAMBDA_DIR/tenant_config.yaml"

cp ../../../core/task_publisher.py \
   "$LAMBDA_DIR/core/"

cp ../../../integrations/messages.py \
   "$LAMBDA_DIR/integrations/"

cp ../../../services/messages_whatsapp.py \
   "$LAMBDA_DIR/services/"

cp ../../../services/messages_dynamodb.py \
   "$LAMBDA_DIR/services/"

cp ../../../models/*.py "$LAMBDA_DIR/models/"

cp "$TENANT_ID/handler.py" \
   "$LAMBDA_DIR/handler.py"

cd "$LAMBDA_DIR"
zip -r $LAMBDA_NAME.zip lambda_function.py tenant_config.yaml handler.py core integrations services models
cd - > /dev/null

rm -rf "$LAMBDA_DIR/core" "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/services" "$LAMBDA_DIR/models" handler.py "$LAMBDA_DIR/tenant_config.yaml"