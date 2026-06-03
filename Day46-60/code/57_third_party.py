"""
Day 57 - 接入三方平台 (Third-Party Platform Integration)

本模块演示了企业级 Web 应用中接入三方平台的四种典型场景：
  1. 短信网关接入 (SMS Gateway)
  2. 第三方登录 / OAuth 2.0 (WeChat Login)
  3. 支付网关接入 (Alipay Payment Gateway)
  4. 通用三方 API 调用 (Generic Third-Party API)

依赖安装:
  pip install requests

注意: 本文件中的密钥、AppID 等均为占位符，实际使用时需替换为真实值。
      部分第三方 SDK (如 alipay-sdk-python) 需额外安装。
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import random
import re
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Optional
from urllib.parse import urlencode

import requests


# ============================================================================
# 公共工具函数
# ============================================================================

def generate_nonce(length: int = 32) -> str:
    """生成随机字符串（nonce），用于请求签名防重放。"""
    chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(random.choices(chars, k=length))


def generate_timestamp() -> int:
    """返回当前 Unix 时间戳（秒）。"""
    return int(time.time())


def sign_with_sha256(params: dict[str, str], secret_key: str) -> str:
    """
    对参数字典按 key 的 ASCII 升序排列后拼接，再用 HMAC-SHA256 签名。

    Args:
        params: 待签名的参数字典
        secret_key: 签名密钥

    Returns:
        十六进制签名字符串
    """
    sorted_items = sorted(params.items())
    sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)
    return hmac.new(
        secret_key.encode("utf-8"),
        sign_str.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def check_mobile_number(tel: str) -> bool:
    """校验中国大陆手机号格式。"""
    pattern = re.compile(r"^1[3-9]\d{9}$")
    return pattern.fullmatch(tel) is not None


def generate_sms_code(length: int = 6) -> str:
    """生成指定位数的纯数字短信验证码。"""
    return "".join(random.choices("0123456789", k=length))


# ============================================================================
# 1. 短信网关接入 (SMS Gateway Integration)
# ============================================================================

@dataclass
class SMSConfig:
    """短信网关配置。"""
    api_url: str
    api_key: str
    signature: str  # 短信签名，如 【Python小课】


class SMSService:
    """
    短信服务 - 演示接入螺丝帽(Luosimao)等短信网关。

    企业应用中常用于：
      - 手机验证码登录
      - 重要消息通知
      - 营销短信推送
    """

    def __init__(self, config: SMSConfig) -> None:
        self.config = config
        # 用简单的字典模拟 Redis 做频率限制与验证码存储
        # 生产环境应替换为 Redis 等分布式缓存
        self._code_store: dict[str, tuple[str, float]] = {}
        self._block_store: dict[str, float] = {}

    def _is_rate_limited(self, mobile: str, cooldown: int = 60) -> bool:
        """检查手机号是否在冷却期内（防重复发送）。"""
        if mobile in self._block_store:
            elapsed = time.time() - self._block_store[mobile]
            if elapsed < cooldown:
                return True
        return False

    def _store_code(self, mobile: str, code: str, ttl: int = 600) -> None:
        """存储验证码，默认有效期 600 秒（10 分钟）。"""
        expire_at = time.time() + ttl
        self._code_store[mobile] = (code, expire_at)

    def verify_code(self, mobile: str, code: str) -> bool:
        """
        校验短信验证码。

        Args:
            mobile: 手机号
            code: 用户提交的验证码

        Returns:
            验证是否通过
        """
        if mobile not in self._code_store:
            return False
        stored_code, expire_at = self._code_store[mobile]
        if time.time() > expire_at:
            del self._code_store[mobile]
            return False
        if stored_code == code:
            del self._code_store[mobile]
            return True
        return False

    def send_sms(self, mobile: str, message: str) -> dict[str, Any]:
        """
        发送短信。

        Args:
            mobile: 目标手机号
            message: 短信内容（需包含签名）

        Returns:
            网关返回的 JSON 响应
        """
        try:
            resp = requests.post(
                url=self.config.api_url,
                auth=("api", self.config.api_key),
                data={"mobile": mobile, "message": message},
                timeout=10,
                verify=True,
            )
            return resp.json()
        except requests.RequestException as e:
            return {"err": -1, "msg": f"网络请求失败: {e}"}

    def send_verification_code(self, mobile: str) -> dict[str, Any]:
        """
        发送短信验证码的业务封装。

        流程:
          1. 校验手机号格式
          2. 检查是否在冷却期内
          3. 生成验证码并存储
          4. 调用短信网关发送

        Args:
            mobile: 手机号

        Returns:
            包含状态码和消息的字典
        """
        if not check_mobile_number(mobile):
            return {"code": 30002, "message": "请输入有效的手机号"}

        if self._is_rate_limited(mobile):
            return {"code": 30001, "message": "请不要在60秒内重复发送短信验证码"}

        code = generate_sms_code()
        message = f"您的短信验证码是{code}，打死也不能告诉别人哟。{self.config.signature}"
        result = self.send_sms(mobile, message)

        if result.get("err") == 0:
            self._store_code(mobile, code)
            self._block_store[mobile] = time.time()
            return {"code": 30000, "message": "短信验证码已发送，请注意查收"}
        else:
            return {"code": 30003, "message": f"短信发送失败: {result.get('msg', '未知错误')}"}


# ============================================================================
# 2. 第三方登录 / OAuth 2.0 (WeChat Login)
# ============================================================================

class OAuthGrantType(str, Enum):
    """OAuth 2.0 授权类型。"""
    AUTHORIZATION_CODE = "authorization_code"
    REFRESH_TOKEN = "refresh_token"


@dataclass
class WeChatConfig:
    """微信开放平台 OAuth 配置。"""
    app_id: str
    app_secret: str
    redirect_uri: str
    # 微信开放平台各端点
    authorize_url: str = "https://open.weixin.qq.com/connect/qrconnect"
    token_url: str = "https://api.weixin.qq.com/sns/oauth2/access_token"
    refresh_url: str = "https://api.weixin.qq.com/sns/oauth2/refresh_token"
    userinfo_url: str = "https://api.weixin.qq.com/sns/userinfo"


@dataclass
class WeChatUserInfo:
    """微信用户信息。"""
    openid: str
    nickname: str
    sex: int
    province: str
    city: str
    country: str
    headimgurl: str
    unionid: Optional[str] = None
    privilege: list[str] = field(default_factory=list)


class WeChatOAuthService:
    """
    微信 OAuth 2.0 登录服务。

    完整流程:
      1. 前端引导用户访问 authorize_url，用户扫码授权
      2. 微信回调 redirect_uri 并携带 code 参数
      3. 后端用 code 换取 access_token + openid
      4. 用 access_token + openid 获取用户信息

    参考文档: https://developers.weixin.qq.com/doc/offiaccount/OA_Web_Apps/Wechat_webpage_authorization.html
    """

    SCOPE_SNSAPI_LOGIN = "snsapi_login"

    def __init__(self, config: WeChatConfig) -> None:
        self.config = config

    def get_authorize_url(self, state: str = "") -> str:
        """
        生成微信 OAuth 授权页面 URL。

        Args:
            state: 用于防止 CSRF 攻击的随机状态值

        Returns:
            完整的授权 URL，前端应引导用户跳转至此地址
        """
        params = {
            "appid": self.config.app_id,
            "redirect_uri": self.config.redirect_uri,
            "response_type": "code",
            "scope": self.SCOPE_SNSAPI_LOGIN,
            "state": state or generate_nonce(16),
        }
        return f"{self.config.authorize_url}?{urlencode(params)}#wechat_redirect"

    def get_access_token(self, code: str) -> dict[str, Any]:
        """
        用授权码换取 access_token。

        Args:
            code: 微信回调时携带的授权码

        Returns:
            包含 access_token, openid, refresh_token 等字段的字典
        """
        params = {
            "appid": self.config.app_id,
            "secret": self.config.app_secret,
            "code": code,
            "grant_type": OAuthGrantType.AUTHORIZATION_CODE.value,
        }
        try:
            resp = requests.get(self.config.token_url, params=params, timeout=10)
            return resp.json()
        except requests.RequestException as e:
            return {"errcode": -1, "errmsg": f"网络请求失败: {e}"}

    def refresh_access_token(self, refresh_token: str) -> dict[str, Any]:
        """
        刷新 access_token（access_token 有效期通常为 2 小时）。

        Args:
            refresh_token: 刷新令牌

        Returns:
            新的 access_token 信息
        """
        params = {
            "appid": self.config.app_id,
            "grant_type": OAuthGrantType.REFRESH_TOKEN.value,
            "refresh_token": refresh_token,
        }
        try:
            resp = requests.get(self.config.refresh_url, params=params, timeout=10)
            return resp.json()
        except requests.RequestException as e:
            return {"errcode": -1, "errmsg": f"网络请求失败: {e}"}

    def get_user_info(self, access_token: str, openid: str) -> WeChatUserInfo | dict[str, Any]:
        """
        获取微信用户基本信息。

        Args:
            access_token: 接口调用凭证
            openid: 用户的唯一标识

        Returns:
            WeChatUserInfo 对象（成功）或错误字典（失败）
        """
        params = {
            "access_token": access_token,
            "openid": openid,
            "lang": "zh_CN",
        }
        try:
            resp = requests.get(self.config.userinfo_url, params=params, timeout=10)
            data = resp.json()
            if "errcode" in data and data["errcode"] != 0:
                return data
            return WeChatUserInfo(
                openid=data["openid"],
                nickname=data.get("nickname", ""),
                sex=data.get("sex", 0),
                province=data.get("province", ""),
                city=data.get("city", ""),
                country=data.get("country", ""),
                headimgurl=data.get("headimgurl", ""),
                unionid=data.get("unionid"),
                privilege=data.get("privilege", []),
            )
        except requests.RequestException as e:
            return {"errcode": -1, "errmsg": f"网络请求失败: {e}"}

    def login_with_code(self, code: str) -> dict[str, Any]:
        """
        一站式登录：用 code 换取 token 并获取用户信息。

        Args:
            code: 授权码

        Returns:
            包含用户信息和 token 的字典
        """
        token_data = self.get_access_token(code)
        if "errcode" in token_data and token_data.get("errcode", 0) != 0:
            return {"success": False, "error": token_data.get("errmsg", "获取token失败")}

        user_info = self.get_user_info(
            token_data["access_token"],
            token_data["openid"],
        )
        if isinstance(user_info, dict) and "errcode" in user_info:
            return {"success": False, "error": user_info.get("errmsg", "获取用户信息失败")}

        return {
            "success": True,
            "user_info": user_info,
            "access_token": token_data["access_token"],
            "refresh_token": token_data["refresh_token"],
            "expires_in": token_data.get("expires_in", 7200),
        }


# ============================================================================
# 3. 支付网关接入 (Alipay Payment Gateway)
# ============================================================================

class AlipayTradeStatus(str, Enum):
    """支付宝交易状态。"""
    WAIT_BUYER_PAY = "WAIT_BUYER_PAY"      # 等待买家付款
    TRADE_CLOSED = "TRADE_CLOSED"            # 交易关闭
    TRADE_SUCCESS = "TRADE_SUCCESS"          # 交易成功
    TRADE_FINISHED = "TRADE_FINISHED"        # 交易完成（不可退款）


@dataclass
class AlipayConfig:
    """支付宝开放平台配置。"""
    app_id: str
    # 应用私钥（用于签名）
    app_private_key: str
    # 支付宝公钥（用于验签）
    alipay_public_key: str
    # 支付宝网关
    gateway_url: str = "https://openapi.alipay.com/gateway.do"
    # 回调地址
    notify_url: str = ""
    # 返回地址（同步回调）
    return_url: str = ""
    # 签名算法
    sign_type: str = "RSA2"
    # 字符编码
    charset: str = "utf-8"
    # API 版本
    version: str = "1.0"
    # 格式
    format_type: str = "json"


@dataclass
class AlipayOrderInfo:
    """支付宝订单信息。"""
    out_trade_no: str       # 商户订单号
    total_amount: str       # 订单金额（单位：元）
    subject: str            # 订单标题
    body: str = ""          # 订单描述
    product_code: str = "FAST_INSTANT_TRADE_PAY"  # 产品码
    timeout_express: str = "30m"  # 超时时间


class AlipayService:
    """
    支付宝支付服务。

    支持的业务场景:
      - 电脑网站支付 (alipay.trade.page.pay)
      - 手机网站支付 (alipay.trade.wap.pay)
      - 交易查询 (alipay.trade.query)
      - 交易退款 (alipay.trade.refund)
      - 异步通知验签

    参考文档: https://open.alipay.com/
    """

    def __init__(self, config: AlipayConfig) -> None:
        self.config = config

    def _build_common_params(self, method: str) -> dict[str, str]:
        """构建公共请求参数。"""
        return {
            "app_id": self.config.app_id,
            "method": method,
            "format": self.config.format_type,
            "charset": self.config.charset,
            "sign_type": self.config.sign_type,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "version": self.config.version,
            "notify_url": self.config.notify_url,
            "return_url": self.config.return_url,
        }

    def _sign_params(self, params: dict[str, str]) -> str:
        """
        对请求参数进行 RSA2 签名。

        实际项目中应使用 alipay-sdk-python 或 cryptography 库实现 RSA 签名，
        此处演示签名逻辑的组装过程。
        """
        # 过滤 sign 参数并排序
        sign_params = {k: v for k, v in params.items() if v and k != "sign"}
        sorted_items = sorted(sign_params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)

        # 实际生产中使用 RSA 私钥签名，此处仅演示流程
        # from cryptography.hazmat.primitives import hashes, serialization
        # from cryptography.hazmat.primitives.asymmetric import padding
        # private_key = serialization.load_pem_private_key(...)
        # signature = private_key.sign(sign_str.encode(), padding.PKCS1v15(), hashes.SHA256())
        # return base64.b64encode(signature).decode()

        return hashlib.sha256(
            (sign_str + self.config.app_private_key).encode("utf-8")
        ).hexdigest()

    def create_page_pay_url(self, order: AlipayOrderInfo) -> str:
        """
        生成电脑网站支付链接。

        用户点击该链接后跳转到支付宝收银台完成付款。

        Args:
            order: 订单信息

        Returns:
            完整的支付宝支付页面 URL
        """
        biz_content = {
            "out_trade_no": order.out_trade_no,
            "total_amount": order.total_amount,
            "subject": order.subject,
            "body": order.body,
            "product_code": order.product_code,
            "timeout_express": order.timeout_express,
        }

        params = self._build_common_params("alipay.trade.page.pay")
        params["biz_content"] = json.dumps(biz_content, ensure_ascii=False)
        params["sign"] = self._sign_params(params)

        return f"{self.config.gateway_url}?{urlencode(params)}"

    def create_wap_pay_url(self, order: AlipayOrderInfo) -> str:
        """
        生成手机网站支付链接。

        Args:
            order: 订单信息

        Returns:
            手机网站支付的完整 URL
        """
        biz_content = {
            "out_trade_no": order.out_trade_no,
            "total_amount": order.total_amount,
            "subject": order.subject,
            "body": order.body,
            "product_code": "QUICK_WAP_WAY",
            "timeout_express": order.timeout_express,
        }

        params = self._build_common_params("alipay.trade.wap.pay")
        params["biz_content"] = json.dumps(biz_content, ensure_ascii=False)
        params["sign"] = self._sign_params(params)

        return f"{self.config.gateway_url}?{urlencode(params)}"

    def query_trade(self, out_trade_no: str, trade_no: str = "") -> dict[str, Any]:
        """
        查询交易状态。

        Args:
            out_trade_no: 商户订单号
            trade_no: 支付宝交易号（与 out_trade_no 二选一）

        Returns:
            交易查询结果
        """
        biz_content: dict[str, str] = {}
        if out_trade_no:
            biz_content["out_trade_no"] = out_trade_no
        if trade_no:
            biz_content["trade_no"] = trade_no

        params = self._build_common_params("alipay.trade.query")
        params["biz_content"] = json.dumps(biz_content, ensure_ascii=False)
        params["sign"] = self._sign_params(params)

        try:
            resp = requests.post(self.config.gateway_url, data=params, timeout=10)
            return resp.json()
        except requests.RequestException as e:
            return {"error": f"查询失败: {e}"}

    def refund_trade(
        self,
        out_trade_no: str,
        refund_amount: str,
        refund_reason: str = "",
        out_request_no: str = "",
    ) -> dict[str, Any]:
        """
        发起交易退款。

        Args:
            out_trade_no: 商户订单号
            refund_amount: 退款金额（单位：元）
            refund_reason: 退款原因
            out_request_no: 退款请求号（部分退款时必传）

        Returns:
            退款结果
        """
        biz_content: dict[str, str] = {
            "out_trade_no": out_trade_no,
            "refund_amount": refund_amount,
        }
        if refund_reason:
            biz_content["refund_reason"] = refund_reason
        if out_request_no:
            biz_content["out_request_no"] = out_request_no

        params = self._build_common_params("alipay.trade.refund")
        params["biz_content"] = json.dumps(biz_content, ensure_ascii=False)
        params["sign"] = self._sign_params(params)

        try:
            resp = requests.post(self.config.gateway_url, data=params, timeout=10)
            return resp.json()
        except requests.RequestException as e:
            return {"error": f"退款失败: {e}"}

    def verify_notify(self, params: dict[str, str]) -> bool:
        """
        验证支付宝异步通知的签名。

        支付宝在用户付款成功后会向 notify_url 发送 POST 请求，
        商户需要验证签名以确保通知来自支付宝而非伪造。

        Args:
            params: 支付宝回调的所有参数

        Returns:
            签名是否合法
        """
        sign = params.get("sign", "")
        sign_type = params.get("sign_type", self.config.sign_type)

        # 移除 sign 和 sign_type
        verify_params = {k: v for k, v in params.items() if k not in ("sign", "sign_type")}

        # 实际生产中应使用支付宝公钥验签
        # 此处演示验签逻辑
        sorted_items = sorted(verify_params.items())
        sign_str = "&".join(f"{k}={v}" for k, v in sorted_items)

        expected = hashlib.sha256(
            (sign_str + self.config.alipay_public_key).encode("utf-8")
        ).hexdigest()

        return sign == expected


# ============================================================================
# 4. 通用三方 API 调用 (Generic Third-Party API)
# ============================================================================

class APIClientError(Exception):
    """三方 API 调用异常。"""

    def __init__(self, code: int, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class APIConfig:
    """通用三方 API 配置。"""
    base_url: str
    api_key: str
    timeout: int = 10
    max_retries: int = 3
    headers: dict[str, str] = field(default_factory=dict)


class ThirdPartyAPIClient:
    """
    通用三方 API 客户端。

    封装了企业级调用三方 API 的通用能力:
      - 统一的请求/响应处理
      - 自动重试机制
      - 请求签名
      - 错误处理

    适用于对接聚合数据、阿里云市场等 API 平台。
    """

    def __init__(self, config: APIConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "Content-Type": "application/json",
            "Accept": "application/json",
            **config.headers,
        })

    def _build_auth_params(self) -> dict[str, str]:
        """构建认证参数。"""
        return {
            "key": self.config.api_key,
            "timestamp": str(generate_timestamp()),
            "nonce": generate_nonce(),
        }

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        发送 GET 请求。

        Args:
            endpoint: API 端点路径
            params: 查询参数

        Returns:
            API 响应的 JSON 数据

        Raises:
            APIClientError: 当 API 返回错误时
        """
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        auth_params = self._build_auth_params()
        if params:
            auth_params.update(params)

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self.session.get(
                    url, params=auth_params, timeout=self.config.timeout
                )
                resp.raise_for_status()
                data = resp.json()
                return data
            except requests.Timeout:
                if attempt == self.config.max_retries:
                    raise APIClientError(-1, "请求超时，已达最大重试次数")
                time.sleep(0.5 * attempt)  # 简单退避
            except requests.RequestException as e:
                raise APIClientError(-1, f"请求异常: {e}")

        return {}

    def post(self, endpoint: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        """
        发送 POST 请求。

        Args:
            endpoint: API 端点路径
            data: 请求体数据

        Returns:
            API 响应的 JSON 数据

        Raises:
            APIClientError: 当 API 返回错误时
        """
        url = f"{self.config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        auth_params = self._build_auth_params()
        body = {**auth_params, **(data or {})}

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self.session.post(url, json=body, timeout=self.config.timeout)
                resp.raise_for_status()
                return resp.json()
            except requests.Timeout:
                if attempt == self.config.max_retries:
                    raise APIClientError(-1, "请求超时，已达最大重试次数")
                time.sleep(0.5 * attempt)
            except requests.RequestException as e:
                raise APIClientError(-1, f"请求异常: {e}")

        return {}


# ============================================================================
# 5. 实名认证服务示例 (Identity Verification)
# ============================================================================

@dataclass
class IdentityVerifyRequest:
    """实名认证请求。"""
    name: str           # 真实姓名
    id_card: str        # 身份证号码
    mobile: str = ""    # 手机号（可选）


@dataclass
class IdentityVerifyResult:
    """实名认证结果。"""
    is_valid: bool
    name: str
    id_card: str
    description: str = ""


class IdentityVerificationService:
    """
    实名认证服务。

    通过三方平台（如聚合数据、阿里云市场等）提供的身份证实名认证 API，
    验证用户姓名与身份证号是否匹配。

    常见应用场景:
      - 用户注册实名
      - 企业认证
      - 金融风控
    """

    def __init__(self, api_client: ThirdPartyAPIClient) -> None:
        self.api_client = api_client

    def verify_identity(self, request: IdentityVerifyRequest) -> IdentityVerifyResult:
        """
        执行实名认证。

        Args:
            request: 认证请求（姓名 + 身份证号）

        Returns:
            认证结果
        """
        try:
            result = self.api_client.post("/identity/verify", {
                "realname": request.name,
                "idcard": request.id_card,
            })
            return IdentityVerifyResult(
                is_valid=result.get("result", {}).get("res") == "1",
                name=request.name,
                id_card=request.id_card,
                description=result.get("result", {}).get("description", ""),
            )
        except APIClientError as e:
            return IdentityVerifyResult(
                is_valid=False,
                name=request.name,
                id_card=request.id_card,
                description=f"认证服务调用失败: {e.message}",
            )


# ============================================================================
# 6. 云存储服务示例 (Cloud Storage)
# ============================================================================

@dataclass
class CloudStorageConfig:
    """云存储配置（以七牛云为例）。"""
    access_key: str
    secret_key: str
    bucket_name: str
    domain: str  # 访问域名，如 http://cdn.example.com


class CloudStorageService:
    """
    云存储服务（演示七牛云接入流程）。

    功能:
      - 生成上传凭证（upload token）
      - 构建文件访问 URL
      - 文件上传（实际上传需安装 qiniu SDK）

    生产环境安装: pip install qiniu
    """

    def __init__(self, config: CloudStorageConfig) -> None:
        self.config = config

    def generate_upload_token(self, key: str, expires: int = 3600) -> str:
        """
        生成七牛云上传凭证。

        前端可使用此 token 直传文件到七牛云，减轻服务器压力。

        Args:
            key: 上传后的文件名
            expires: token 有效期（秒）

        Returns:
            上传凭证字符串
        """
        # 实际应使用 qiniu.Auth 生成
        # import qiniu
        # auth = qiniu.Auth(self.config.access_key, self.config.secret_key)
        # return auth.upload_token(self.config.bucket_name, key, expires)

        # 演示：基于 HMAC 模拟生成 token
        policy = {
            "scope": f"{self.config.bucket_name}:{key}",
            "deadline": int(time.time()) + expires,
        }
        policy_str = json.dumps(policy, ensure_ascii=False)
        import base64
        encoded_policy = base64.urlsafe_b64encode(policy_str.encode()).decode()
        sign = hmac.new(
            self.config.secret_key.encode(),
            encoded_policy.encode(),
            hashlib.sha1,
        ).digest()
        import base64
        encoded_sign = base64.urlsafe_b64encode(sign).decode()
        return f"{self.config.access_key}:{encoded_sign}:{encoded_policy}"

    def get_file_url(self, key: str) -> str:
        """
        获取文件访问 URL。

        Args:
            key: 文件名/路径

        Returns:
            完整的文件访问地址
        """
        return f"{self.config.domain.rstrip('/')}/{key}"

    def generate_unique_filename(self, original_filename: str) -> str:
        """
        生成唯一文件名，避免冲突。

        Args:
            original_filename: 原始文件名

        Returns:
            UUID + 原扩展名的新文件名
        """
        _, ext = os.path.splitext(original_filename)
        return f"{uuid.uuid4().hex}{ext}"


# ============================================================================
# 综合演示 (main guard)
# ============================================================================

def demo_sms_service() -> None:
    """演示短信验证码服务。"""
    print("=" * 60)
    print("  短信网关服务演示 (SMS Gateway)")
    print("=" * 60)

    config = SMSConfig(
        api_url="http://sms-api.luosimao.com/v1/send.json",
        api_key="your-api-key-here",
        signature="【Python小课】",
    )
    sms_service = SMSService(config)

    # 测试手机号校验
    test_numbers = ["13800138000", "12345678", "138001380001", "15912345678"]
    print("\n手机号格式校验:")
    for num in test_numbers:
        valid = check_mobile_number(num)
        print(f"  {num} -> {'有效' if valid else '无效'}")

    # 测试验证码生成
    print(f"\n生成验证码: {generate_sms_code()}")
    print(f"生成验证码: {generate_sms_code(4)}")

    # 模拟发送流程（不会真正发送，因为是占位 API Key）
    print("\n模拟发送短信验证码:")
    mobile = "13800138000"
    result = sms_service.send_verification_code(mobile)
    print(f"  手机号: {mobile}")
    print(f"  结果: {result}")

    # 模拟验证码校验
    if mobile in sms_service._code_store:
        stored_code = sms_service._code_store[mobile][0]
        print(f"\n模拟验证码校验:")
        print(f"  输入正确验证码 '{stored_code}': {sms_service.verify_code(mobile, stored_code)}")
        print(f"  输入错误验证码 '000000': {sms_service.verify_code(mobile, '000000')}")


def demo_wechat_oauth() -> None:
    """演示微信 OAuth 登录服务。"""
    print("\n" + "=" * 60)
    print("  微信 OAuth 2.0 登录演示 (WeChat Login)")
    print("=" * 60)

    config = WeChatConfig(
        app_id="wx1234567890abcdef",
        app_secret="your-app-secret-here",
        redirect_uri="https://example.com/callback/wechat",
    )
    wechat_service = WeChatOAuthService(config)

    # 生成授权 URL
    state = generate_nonce(16)
    auth_url = wechat_service.get_authorize_url(state)
    print(f"\n1. 授权 URL（引导用户访问此地址扫码登录）:")
    print(f"   {auth_url}")

    print(f"\n2. 用户授权后，微信会回调 redirect_uri 并携带 code 参数")
    print(f"   例如: https://example.com/callback/wechat?code=AUTH_CODE&state={state}")

    print(f"\n3. 后端使用 code 调用 get_access_token() 换取 token")
    print(f"   token_data = wechat_service.get_access_token('SAMPLE_CODE')")

    print(f"\n4. 使用 token 获取用户信息")
    print(f"   user_info = wechat_service.get_user_info(access_token, openid)")

    print(f"\n5. 或者使用一站式登录方法:")
    print(f"   result = wechat_service.login_with_code('SAMPLE_CODE')")

    # 演示完整流程（code 无效会返回错误，仅展示调用方式）
    print(f"\n模拟调用 login_with_code（code 无效，会返回错误信息）:")
    result = wechat_service.login_with_code("sample_invalid_code")
    print(f"   结果: {json.dumps(result, ensure_ascii=False, indent=2)}")


def demo_alipay_payment() -> None:
    """演示支付宝支付服务。"""
    print("\n" + "=" * 60)
    print("  支付宝支付网关演示 (Alipay Payment)")
    print("=" * 60)

    config = AlipayConfig(
        app_id="2021000000000000",
        app_private_key="your-app-private-key",
        alipay_public_key="your-alipay-public-key",
        notify_url="https://example.com/callback/alipay/notify",
        return_url="https://example.com/callback/alipay/return",
    )
    alipay_service = AlipayService(config)

    # 创建订单
    order = AlipayOrderInfo(
        out_trade_no=f"ORDER_{uuid.uuid4().hex[:16].upper()}",
        total_amount="99.00",
        subject="Python进阶课程",
        body="Python 100天从新手到大师 - 进阶课程",
    )

    print(f"\n订单信息:")
    print(f"  订单号: {order.out_trade_no}")
    print(f"  金额: {order.total_amount} 元")
    print(f"  标题: {order.subject}")

    # 生成电脑网站支付 URL
    pc_pay_url = alipay_service.create_page_pay_url(order)
    print(f"\n电脑网站支付 URL:")
    print(f"  {pc_pay_url[:100]}...")

    # 生成手机网站支付 URL
    wap_pay_url = alipay_service.create_wap_pay_url(order)
    print(f"\n手机网站支付 URL:")
    print(f"  {wap_pay_url[:100]}...")

    # 模拟异步通知验签
    print(f"\n异步通知验签演示:")
    mock_notify_params = {
        "trade_no": "2023120122001400001",
        "out_trade_no": order.out_trade_no,
        "trade_status": "TRADE_SUCCESS",
        "total_amount": order.total_amount,
        "sign": "mock_signature",
        "sign_type": "RSA2",
    }
    is_valid = alipay_service.verify_notify(mock_notify_params)
    print(f"  验签结果: {'通过' if is_valid else '失败'}（演示环境签名不匹配属正常现象）")

    # 展示退款调用方式
    print(f"\n退款调用示例:")
    print(f"  result = alipay_service.refund_trade(")
    print(f"      out_trade_no='{order.out_trade_no}',")
    print(f"      refund_amount='99.00',")
    print(f"      refund_reason='用户申请退款'")
    print(f"  )")


def demo_third_party_api() -> None:
    """演示通用三方 API 与实名认证服务。"""
    print("\n" + "=" * 60)
    print("  通用三方 API 与实名认证演示")
    print("=" * 60)

    # 创建通用 API 客户端
    api_config = APIConfig(
        base_url="https://api.juhe.cn",
        api_key="your-juhe-api-key",
        timeout=10,
        max_retries=3,
    )
    api_client = ThirdPartyAPIClient(api_config)

    print(f"\n通用 API 客户端配置:")
    print(f"  Base URL: {api_config.base_url}")
    print(f"  超时: {api_config.timeout}s")
    print(f"  最大重试: {api_config.max_retries} 次")

    # 实名认证服务
    verify_service = IdentityVerificationService(api_client)
    verify_request = IdentityVerifyRequest(
        name="张三",
        id_card="110101199001011234",
        mobile="13800138000",
    )

    print(f"\n实名认证请求:")
    print(f"  姓名: {verify_request.name}")
    print(f"  身份证: {verify_request.id_card}")

    # 注意：实际调用会因 API Key 无效而失败
    print(f"\n（注：实际调用需替换为有效的 API Key）")


def demo_cloud_storage() -> None:
    """演示云存储服务。"""
    print("\n" + "=" * 60)
    print("  云存储服务演示 (七牛云 Qiniu)")
    print("=" * 60)

    config = CloudStorageConfig(
        access_key="your-access-key",
        secret_key="your-secret-key",
        bucket_name="mybucket",
        domain="http://cdn.example.com",
    )
    storage_service = CloudStorageService(config)

    # 生成唯一文件名
    original = "我的照片.jpg"
    unique_name = storage_service.generate_unique_filename(original)
    print(f"\n文件名生成:")
    print(f"  原始: {original}")
    print(f"  唯一: {unique_name}")

    # 生成上传凭证
    token = storage_service.generate_upload_token(unique_name)
    print(f"\n上传凭证 (token):")
    print(f"  {token[:80]}...")

    # 获取访问 URL
    file_url = storage_service.get_file_url(unique_name)
    print(f"\n文件访问 URL:")
    print(f"  {file_url}")

    print(f"\n生产环境使用方法:")
    print(f"  pip install qiniu")
    print(f"  import qiniu")
    print(f"  auth = qiniu.Auth(access_key, secret_key)")
    print(f"  token = auth.upload_token(bucket_name, key)")
    print(f"  qiniu.put_file(token, key, file_path)")


def show_architecture_summary() -> None:
    """展示三方平台接入的整体架构总结。"""
    print("\n" + "=" * 60)
    print("  三方平台接入架构总结")
    print("=" * 60)

    summary = """
    企业级 Web 应用接入三方平台的两种方式:

    1. API 接入 (通过 HTTP 请求调用三方接口)
       - 适用场景: 聚合数据、天气查询、身份证认证等
       - 技术要点: HTTP 请求、JSON 解析、请求签名、重试机制

    2. SDK 接入 (通过安装三方库调用封装好的方法)
       - 适用场景: 支付宝SDK、七牛云SDK、微信SDK等
       - 技术要点: pip install、初始化配置、调用封装方法

    核心安全措施:
       [1] 请求签名 (HMAC-SHA256 / RSA2) - 防篡改
       [2] Nonce + Timestamp - 防重放攻击
       [3] HTTPS - 传输加密
       [4] IP 白名单 - 限制调用来源
       [5] 异步通知验签 - 确保回调真实性

    本模块涵盖的场景:
       +---------------------+--------------------------------+
       | 场景                | 演示类                          |
       +---------------------+--------------------------------+
       | 短信验证码          | SMSService                     |
       | 微信 OAuth 登录     | WeChatOAuthService             |
       | 支付宝支付          | AlipayService                  |
       | 通用三方 API        | ThirdPartyAPIClient            |
       | 实名认证            | IdentityVerificationService    |
       | 云存储              | CloudStorageService            |
       +---------------------+--------------------------------+
    """
    print(summary)


if __name__ == "__main__":
    print("Day 57 - 接入三方平台 (Third-Party Platform Integration)")
    print("=" * 60)

    show_architecture_summary()
    demo_sms_service()
    demo_wechat_oauth()
    demo_alipay_payment()
    demo_third_party_api()
    demo_cloud_storage()

    print("\n" + "=" * 60)
    print("  运行完毕。以上为各三方平台接入的演示代码。")
    print("  实际使用时请将占位密钥替换为真实密钥。")
    print("=" * 60)
