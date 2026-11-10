"""独立连通性测试：运行一次请求，不导入页面、不在 import 时调用 API。"""
import logging
from pathlib import Path

from dotenv import dotenv_values
from openai import APIConnectionError, APIStatusError, APITimeoutError, OpenAI

ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
MODEL = "gpt-6-luna"


def error_hint(error):
    """仅返回固定提示，不输出服务端正文、请求头或异常原文。"""
    if isinstance(error, APITimeoutError):
        return "网络请求超时：请检查网络或代理后重试；本程序不会自动重试。"
    if isinstance(error, APIConnectionError):
        return "网络连接失败：请检查网络、代理、DNS 或 TLS 证书。"
    body = error.body if isinstance(error.body, dict) else {}
    detail = body.get("error", body)
    detail = detail if isinstance(detail, dict) else {}
    code = detail.get("code") or getattr(error, "code", None)
    kind = detail.get("type")
    if error.status_code == 401:
        return "API 密钥认证失败：请检查根目录 .env 中的 OPENAI_API_KEY 是否有效或已被撤销。"
    if code in {"insufficient_quota", "billing_hard_limit_reached", "billing_not_active"} or kind == "insufficient_quota":
        return "API 额度不足或计费未启用：请检查 API 账户余额、项目预算与计费状态。"
    if code in {"model_not_found", "model_not_available", "unsupported_model"} or error.status_code == 404:
        return "模型不可用：gpt-6-luna 不存在、当前项目无访问权限，或该接口不支持它；未自动更换模型。"
    if error.status_code == 403:
        return "访问被拒绝：请检查项目/密钥权限、模型访问权限及账户访问限制。"
    if error.status_code == 429:
        return "请求速率受限：请稍后重试；服务端未明确报告余额不足。"
    if error.status_code >= 500:
        return "OpenAI 服务暂时异常：请稍后重试。"
    return "API 请求被拒绝：请检查 SDK、模型及 Responses API 参数配置（未打印原始错误）。"


def main():
    # 即使用户启用了 SDK 调试日志，也不让日志输出请求信息。
    for name in ("openai", "httpx", "httpcore", "dotenv.main"):
        logging.getLogger(name).disabled = True
    if not ENV_PATH.is_file():
        print("未找到项目根目录 .env，请添加 OPENAI_API_KEY 后运行。")
        return 1
    try:
        # dotenv_values 是 python-dotenv 的只读加载接口；不修改进程环境，
        # 不使用其他目录或系统环境中的 Key 替代本次要测试的 .env。
        config = dotenv_values(ENV_PATH, encoding="utf-8-sig", interpolate=False)
        key = (config.get("OPENAI_API_KEY") or "").strip()
    except (OSError, UnicodeError):
        print("无法读取 .env，请检查文件权限与 UTF-8 编码。")
        return 1
    if not key:
        print("根目录 .env 未配置非空 OPENAI_API_KEY；没有发送请求。")
        return 1
    print(f"已读取 OPENAI_API_KEY（不显示内容）。正在请求 {MODEL}，关闭自动重试。")
    try:
        with OpenAI(api_key=key, base_url="https://api.openai.com/v1",
                    timeout=30.0, max_retries=0) as client:
            response = client.responses.create(
                model=MODEL,
                input="请只用一句简短中文回复：API 连通性测试成功。",
                max_output_tokens=128,
                store=False,
            )
        text = response.output_text
        if text:
            print("模型返回：")
            print(text.replace(key, "[密钥已隐藏]"))
        if response.status != "completed" or not text:
            print("已收到 API 响应，但未获得完整文本结果；本次测试未完全通过，没有自动追加请求。")
            return 1
        print("Responses API 连通性测试通过。")
        return 0
    except (APIConnectionError, APIStatusError) as error:
        print(error_hint(error))
        return 1
    except Exception:
        print("本地配置、SDK 或响应处理异常；为保护密钥，不输出异常原文。请检查依赖版本和配置。")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
