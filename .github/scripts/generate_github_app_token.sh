#!/usr/bin/env bash

# GitHub App のトークンを生成するスクリプト
# 参考: https://zenn.dev/tmknom/articles/github-apps-token

# Base64URLエンコード関数
base64url() {
  openssl enc -base64 -A | tr '+/' '-_' | tr -d '='
}

# 署名する関数
sign() {
  openssl dgst -binary -sha256 -sign <(printf '%s' "${PRIVATE_KEY}")
}

# JWTのヘッダー
header="$(printf '{"alg":"RS256","typ":"JWT"}' | base64url)"
# JWTのペイロード
now="$(date '+%s')"
iat="$((now - 60))"
exp="$((now + (3 * 60)))"
template='{"iss":"%s","iat":%s,"exp":%s}'
payload="$(printf "${template}" "${APP_ID}" "${iat}" "${exp}" | base64url)"
echo "::add-mask::${payload}"
# JWTの署名
signature="$(printf '%s' "${header}.${payload}" | sign | base64url)"
echo "::add-mask::${signature}"
# JWTの生成
jwt="${header}.${payload}.${signature}"
echo "::add-mask::${jwt}"

# Installtion ID を取得
installation_id="$(curl --location --silent --request GET \
  --url "${GITHUB_API_URL}/repos/${GITHUB_REPOSITORY}/installation" \
  --header "Accept: application/vnd.github+json" \
  --header "X-GitHub-Api-Version: 2022-11-28" \
  --header "Authorization: Bearer ${jwt}" \
  | jq -r '.id'
)"

# アクションを実行するリポジトリ名を取得
repo_name="$(echo "${GITHUB_REPOSITORY}" | cut -d '/' -f 2)"
# アクセストークンを生成
token="$(curl --location --silent --request POST \
  --url "${GITHUB_API_URL}/app/installations/${installation_id}/access_tokens" \
  --header "Accept: application/vnd.github+json" \
  --header "X-GitHub-Api-Version: 2022-11-28" \
  --header "Authorization: Bearer ${jwt}" \
  --data "$(printf '{"repositories":["%s"]}' "${repo_name}")" \
  | jq -r '.token'
)"
echo "::add-mask::${token}"
echo "token=${token}" >>"${GITHUB_OUTPUT}"