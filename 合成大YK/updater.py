"""启动时自动检查更新。

从远程 URL 获取最新版本号，与本地比较。
如有新版本，通过回调通知主程序显示提示。
"""

import json
import threading
from urllib.request import urlopen, Request
from urllib.error import URLError

# 更新检查配置
UPDATE_CHECK_TIMEOUT = 5  # 秒

# 离线备用（本地记录上次检查到的远程版本）
_OFFLINE_STORE = None


def _parse_version(version_str: str) -> tuple[int, ...]:
    """解析版本号字符串为可比较的元组（统一4段）。
    支持格式: 'v0.3.2.0' 或 '0.3.2' 或 '1.0'"""
    v = version_str.strip().lstrip("v").split("-")[0]  # 去掉 v 前缀和 -beta 等后缀
    try:
        parts = [int(x) for x in v.split(".")]
    except ValueError:
        parts = [0, 0, 0, 0]
    # 补齐到4段
    while len(parts) < 4:
        parts.append(0)
    return tuple(parts[:4])


def check_update(config: dict, on_result, on_error=None):
    """异步检查更新。

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
