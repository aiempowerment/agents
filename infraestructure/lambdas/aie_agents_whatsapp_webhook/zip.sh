#!/bin/bash
set -e

LAMBDA_DIR="$(cd "$(dirname "$0")" && pwd)"

rm -f "$LAMBDA_DIR/aie_agents_whatsapp_webhook.zip"

mkdir -p "$LAMBDA_DIR/integrations"
mkdir -p "$LAMBDA_DIR/services"
mkdir -p "$LAMBDA_DIR/models"

cp ../../../integrations/messages.py \
   "$LAMBDA_DIR/integrations/"

cp ../../../services/messages_whatsapp.py \
   "$LAMBDA_DIR/services/"

cp ../../../services/messages_dynamodb.py \
   "$LAMBDA_DIR/services/"

cp ../../../models/message.py \
   "$LAMBDA_DIR/models/"

cd "$LAMBDA_DIR"
zip -r aie_agents_whatsapp_webhook.zip lambda_function.py integrations services models
cd - > /dev/null

rm -rf "$LAMBDA_DIR/integrations" "$LAMBDA_DIR/services" "$LAMBDA_DIR/models"