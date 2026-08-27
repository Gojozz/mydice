#!/usr/bin/env bash
read -p "Masukkan Client ID: " CLIENT_ID
read -p "Masukkan Client Secret: " CLIENT_SECRET

URL="https://accounts.google.com/o/oauth2/v2/auth?client_id=${CLIENT_ID}&redirect_uri=http://127.0.0.1&response_type=code&scope=https://www.googleapis.com/auth/youtube.force-ssl&access_type=offline&prompt=consent"

echo -e "\n--------------------------------------------------"
echo -e "1. Buka URL ini di Browser (Chrome):\n${URL}"
echo -e "--------------------------------------------------\n"

read -p "2. Paste Kode Otorisasi (karakter setelah 'code='): " CODE

echo -e "\n=========================================="
echo "REFRESH TOKEN ANDA:"

curl -s -X POST https://oauth2.googleapis.com/token \
  -d "client_id=${CLIENT_ID}" \
  -d "client_secret=${CLIENT_SECRET}" \
  -d "code=${CODE}" \
  -d "grant_type=authorization_code" \
  -d "redirect_uri=http://127.0.0.1" | jq -r '.refresh_token'

echo -e "==========================================\n"
