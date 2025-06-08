from contextvars import ContextVar

# 使用 ContextVar 来存储当前请求的租户ID，确保在异步环境中上下文安全
tenant_id_context: ContextVar[str] = ContextVar("tenant_id_context")
