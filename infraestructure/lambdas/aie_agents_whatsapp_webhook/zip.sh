#!/bin/bash
set -e

TENANT_ID="${1:?Usage: $0 <tenant_id>}"

LAMBDA_DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$LAMBDA_DIR/aie_agents_whatsapp_webhook.zip"

mkdir -p "$LAMBDA_DIR/core"
mkdir -p "$LAMBDA_DIR/integrations"
mkdir -p "$LAMBDA_DIR/services"
mkdir -p "$LAMBDA_DIR/models"

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
zip -r aie_agents_whatsapp_webhook.zip lambda_function.py handler.py core integrations services models
cd - > /dev/null

rm -rf "$LAMBDA_DIR/core" "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/services" "$LAMBDA_DIR/models" handler.py