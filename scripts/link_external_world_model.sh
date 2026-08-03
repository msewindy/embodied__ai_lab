#!/usr/bin/env bash
# 将本机「世界模型」资料目录以 symlink 挂到 external/world_model
# - 不复制文件，不创建 Git Submodule
# - 挂载点已被 .gitignore 忽略
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LINK_PATH="${REPO_ROOT}/external/world_model"
EXTERNAL_DIR="${REPO_ROOT}/external"
PARENT_DIR="$(dirname "${REPO_ROOT}")"
SOURCE_PATH="${1:-}"

find_sibling() {
  local d name
  for d in "${PARENT_DIR}"/*; do
    [[ -d "$d" ]] || continue
    name="$(basename "$d")"
    # lab-ws-02: world_model；Windows 侧常见：世界模型
    if [[ "$name" == "world_model" || "$name" == *世界模型* || "$name" == *world*model* ]]; then
      if [[ -f "$d/README.md" && -d "$d/docs" ]]; then
        printf '%s\n' "$d"
        return 0
      fi
    fi
  done
  return 1
}

if [[ -z "${SOURCE_PATH}" ]]; then
  SOURCE_PATH="$(find_sibling || true)"
fi

if [[ -z "${SOURCE_PATH}" || ! -d "${SOURCE_PATH}" ]]; then
  echo "未找到源目录。用法:" >&2
  echo "  $0 [/path/to/world_model]" >&2
  echo "当前仓库: ${REPO_ROOT}" >&2
  echo "已扫描父目录: ${PARENT_DIR}" >&2
  exit 1
fi

SOURCE_PATH="$(cd "${SOURCE_PATH}" && pwd)"
mkdir -p "${EXTERNAL_DIR}"

if [[ -L "${LINK_PATH}" ]]; then
  echo "移除已有 symlink: ${LINK_PATH}"
  rm -f "${LINK_PATH}"
elif [[ -e "${LINK_PATH}" ]]; then
  echo "路径已存在且不是 symlink，请手动处理: ${LINK_PATH}" >&2
  exit 1
fi

ln -s "${SOURCE_PATH}" "${LINK_PATH}"
echo "OK: ${LINK_PATH} -> ${SOURCE_PATH}"

if [[ -f "${LINK_PATH}/README.md" ]]; then
  ls -ld "${LINK_PATH}"
  echo "可读: ${LINK_PATH}/README.md"
else
  echo "警告: 挂载成功但未找到 README.md" >&2
fi
