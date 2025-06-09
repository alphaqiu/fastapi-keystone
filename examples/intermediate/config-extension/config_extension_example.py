"""
配置扩展机制使用示例

这个示例展示了如何使用 fastapi-keystone 的配置扩展机制来支持自定义配置段。
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings

from fastapi_keystone.config import load_config


# 定义扩展配置类
class RedisConfig(BaseSettings):
    """Redis配置"""

    host: str = Field(default="127.0.0.1", description="Redis服务器地址")
    port: int = Field(default=6379, description="Redis端口")
    password: Optional[str] = Field(default=None, description="Redis密码")
    database: int = Field(default=0, description="Redis数据库编号")
    max_connections: int = Field(default=10, description="最大连接数")
    enable: bool = Field(default=True, description="是否启用Redis")


class EmailConfig(BaseSettings):
    """邮件配置"""

    smtp_host: str = Field(description="SMTP服务器地址")
    smtp_port: int = Field(default=587, description="SMTP端口")
    username: str = Field(description="邮箱用户名")
    password: str = Field(description="邮箱密码")
    use_tls: bool = Field(default=True, description="是否使用TLS")
    from_address: str = Field(description="发件人地址")


class CacheConfig(BaseSettings):
    """缓存配置"""

    type: str = Field(default="redis", description="缓存类型")
    ttl: int = Field(default=3600, description="默认TTL（秒）")
    prefix: str = Field(default="app:", description="缓存键前缀")
    enable_compression: bool = Field(default=False, description="是否启用压缩")


class AuthConfig(BaseSettings):
    """认证配置"""

    secret_key: str = Field(description="JWT密钥")
    algorithm: str = Field(default="HS256", description="JWT算法")
    access_token_expire_minutes: int = Field(
        default=30, description="访问令牌过期时间（分钟）"
    )
    refresh_token_expire_days: int = Field(
        default=7, description="刷新令牌过期时间（天）"
    )
    enable_refresh_token: bool = Field(default=True, description="是否启用刷新令牌")


def main():
    """演示配置扩展机制的使用"""
    print("=== FastAPI Keystone 配置扩展机制演示 ===\n")

    # 支持JSON和YAML两种格式
    print("[1] 加载JSON配置:")
    config = load_config("config.example.json")
    print(f"   服务器: {config.server.host}:{config.server.port}")
    print(f"   运行模式: {config.server.run_mode}")

    print("\n[2] 加载YAML配置:")
    config_yaml = load_config("config.example.yaml")
    print(f"   服务器: {config_yaml.server.host}:{config_yaml.server.port}")
    print(f"   运行模式: {config_yaml.server.run_mode}")

    print("\n1. 基础配置信息:")
    print(f"   日志级别: {config.logger.level}")
    default_db = config.databases["default"]
    if default_db:
        print(f"   数据库: {default_db.host}")
    else:
        print("   数据库: 未配置")

    print("\n2. 检查扩展配置段:")
    available_sections = config.get_section_keys()
    print(f"   可用的扩展配置段: {available_sections}")

    print("\n3. 加载并使用扩展配置:")

    # 加载Redis配置
    if config.has_section("redis"):
        redis_config = config.get_section("redis", RedisConfig)
        if redis_config and redis_config.enable:
            print(
                f"   ✓ Redis: {redis_config.host}:{redis_config.port} (DB {redis_config.database})"
            )
        else:
            print("   ✗ Redis: 已禁用")
    else:
        print("   ✗ Redis: 配置不存在")

    # 加载邮件配置
    if config.has_section("email"):
        email_config = config.get_section("email", EmailConfig)
        if email_config:
            print(
                f"   ✓ Email: {email_config.smtp_host}:{email_config.smtp_port} (TLS: {email_config.use_tls})"
            )
            print(f"     发件人: {email_config.from_address}")
    else:
        print("   ✗ Email: 配置不存在")

    # 加载缓存配置
    if config.has_section("cache"):
        cache_config = config.get_section("cache", CacheConfig)
        if cache_config:
            print(
                f"   ✓ Cache: {cache_config.type} (TTL: {cache_config.ttl}s, 前缀: {cache_config.prefix})"
            )
    else:
        print("   ✗ Cache: 配置不存在")

    # 加载认证配置
    if config.has_section("auth"):
        auth_config = config.get_section("auth", AuthConfig)
        if auth_config:
            print(
                f"   ✓ Auth: {auth_config.algorithm} (Token过期: {auth_config.access_token_expire_minutes}分钟)"
            )
    else:
        print("   ✗ Auth: 配置不存在")

    print("\n4. 缓存机制演示:")
    # 第一次加载（从配置文件解析）
    redis_config1 = config.get_section("redis", RedisConfig)
    print(f"   第一次加载Redis配置: {id(redis_config1)}")

    # 第二次加载（从缓存获取）
    redis_config2 = config.get_section("redis", RedisConfig)
    print(f"   第二次加载Redis配置: {id(redis_config2)}")
    print(f"   是否为同一对象: {redis_config1 is redis_config2}")

    print("\n5. 错误处理演示:")
    try:
        # 尝试加载不存在的配置段
        missing_config = config.get_section("nonexistent", RedisConfig)
        print(f"   不存在的配置段结果: {missing_config}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\n6. 缓存管理:")
    print(f"   清除前缓存数量: {len(config._section_cache)}")
    config.clear_section_cache("redis")
    print(f"   清除redis缓存后: {len(config._section_cache)}")
    config.clear_section_cache()
    print(f"   清除所有缓存后: {len(config._section_cache)}")

    print("\n=== 演示完成 ===")


if __name__ == "__main__":
    main()
