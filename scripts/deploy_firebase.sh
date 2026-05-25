#!/usr/bin/env zsh
set -euo pipefail

if ! command -v firebase >/dev/null 2>&1; then
  echo "firebase CLI is required: npm install -g firebase-tools"
  exit 1
fi

if [[ ! -f apps/web/.env ]]; then
  cp apps/web/.env.example apps/web/.env
fi

echo "Building frontend..."
(cd apps/web && npm install && npm run build)

echo "Deploying to Firebase Hosting..."
firebase deploy --only hosting
