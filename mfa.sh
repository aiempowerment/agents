#!/bin/sh

PROFILE_BASE="base"
PROFILE_TARGET="default"

echo "Enter MFA Code:"
read MFA_CODE

value=$(aws sts get-session-token \
  --serial-number arn:aws:iam::355622872251:mfa/aie \
  --token-code $MFA_CODE \
  --profile $PROFILE_BASE)

access_key_id=$(echo $value | jq -r '.Credentials.AccessKeyId')
secret_access_key=$(echo $value | jq -r '.Credentials.SecretAccessKey')
session_token=$(echo $value | jq -r '.Credentials.SessionToken')

aws configure set aws_access_key_id     "$access_key_id"     --profile $PROFILE_TARGET
aws configure set aws_secret_access_key "$secret_access_key" --profile $PROFILE_TARGET
aws configure set aws_session_token     "$session_token"     --profile $PROFILE_TARGET

echo "Updated profile [$PROFILE_TARGET] with MFA session token."