"""启动时自动检查更新。

v2.2.2.4: 对接 GitHub Releases API。
  - 查询 https://api.github.com/repos/{owner}/{repo}/releases/latest
  - 解析 tag_name 获版本号，在 assets 中找含 "Setup" 的下载链接
  - 同时保留旧式自定义 URL 接口（check_update / check_update_simple）
"""

import json
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError

# ── GitHub Releases API ──────────────────────────────────────
GITHUB_API = "https://api.github.com/repos/wanchengyang2010/big-alloy-merge/releases/latest"

# ── 超时 ─────────────────────────────────────────────────────
UPDATE_CHECK_TIMEOUT = 5  # 秒


def _parse_version(version_str: str) -> tuple[int, ...]:
    """解析版本号字符串为可比较的元组（统一4段）。
    支持格式: 'v0.3.2.0' 或 '0.3.2' 或 '1.0'"""
    v = version_str.strip().lstrip("v").split("-")[0]
    try:
        parts = [int(x) for x in v.split(".")]
    except ValueError:
        parts = [0, 0, 0, 0]
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def check_github_update(current_version: str, on_result, on_error=None):
    """从 GitHub Releases 检查更新（v2.2.2.4）。

    参数:
        current_version: 当前版本号字符串（如 "v2.2.2.4"）
        on_result(has_update, latest_version, download_url): 检查完成回调
        on_error(error_msg): 出错回调（可选）

    GitHub API 返回格式:
        {"tag_name": "v2.2.2.4", "assets": [{"name": "…Setup….exe",
         "browser_download_url": "https://…"}]}

    找到含 "Setup" 的 asset → 下载链接；找不到 → 取第一个 asset。
    """
    def _do_check():
        try:
            req = Request(GITHUB_API, headers={
                "User-Agent": "BigAlloyMerge-Updater/2.0",
                "Accept": "application/vnd.github+json",
            })
            with urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tag = data.get("tag_name", "")
            if not tag:
                if on_error:
                    on_error("GitHub 返回数据无效：无 tag_name")
                return

            remote_version = tag
            assets = data.get("assets", [])
            download_url = ""

            # 优先找含 "Setup" 的安装包
            for a in assets:
                name = a.get("name", "")
                if "Setup" in name:
                    download_url = a.get("browser_download_url", "")
                    break

            # 无 Setup → 取第一个 asset 的下载链接
            if not download_url and assets:
                download_url = assets[0].get("browser_download_url", "")

            current_parsed = _parse_version(current_version)
            remote_parsed = _parse_version(remote_version)

            if remote_parsed > current_parsed:
                on_result(True, remote_version, download_url)
            else:
                on_result(False, remote_version, download_url)

        except URLError as e:
            if on_error:
                on_error(f"网络连接失败：{e.reason}")
        except json.JSONDecodeError:
            if on_error:
                on_error("GitHub 版本数据格式错误")
        except Exception as e:
            if on_error:
                on_error(f"检查更新失败：{e}")

    thread = threading.Thread(target=_do_check, daemon=True)
    thread.start()
    return thread


# ── 旧式接口（向后兼容）──────────────────────────────────────

def check_update(config: dict, on_result, on_error=None):
    """异步检查更新（自定义 URL 版本）。

    参数:
        config: {'version_url': str, 'download_url': str, 'current_version': str}
        on_result(has_update, latest_version, download_url): 检查完成回调
        on_error(error_msg): 出错回调（可选）
    """
    url = config.get("version_url", "")
    current = config.get("current_version", "v0.0.0.0")
    download_url = config.get("download_url", "")

    if not url:
        if on_error:
            on_error("未配置更新检查 URL")
        return

    def _do_check():
        try:
            req = Request(url, headers={"User-Agent": "BigAlloyMerge-Updater/1.0"})
            with urlopen(req, timeout=UPDATE_CHECK_TIMEOUT) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_version = data.get("version", "")
                remote_download = data.get("download_url", download_url)

            if not remote_version:
                if on_error:
                    on_error("远程版本信息无效")
                return

            current_parsed = _parse_version(current)
            remote_parsed = _parse_version(remote_version)

            if remote_parsed > current_parsed:
                on_result(True, remote_version, remote_download)
            else:
                on_result(False, remote_version, remote_download)

        except URLError as e:
            if on_error:
                on_error(f"网络连接失败：{e.reason}")
        except json.JSONDecodeError:
            if on_error:
                on_error("远程版本数据格式错误")
        except Exception as e:
            if on_error:
                on_error(f"检查更新失败：{e}")

    thread = threading.Thread(target=_do_check, daemon=True)
    thread.start()
    return thread


def check_update_simple(version_url: str, current_version: str, callback):
    """简化接口：只需要 URL 和当前版本，有更新时回调。
    callback(has_update, latest_version, download_url)
    """
    config = {
        "version_url": version_url,
        "download_url": "",
        "current_version": current_version,
    }
    return check_update(config, callback)
