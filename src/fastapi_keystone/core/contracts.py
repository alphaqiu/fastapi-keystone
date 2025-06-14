from __future__ import annotations

from logging import Logger
from typing import (
    Any,
    Awaitable,
    Callable,
    List,
    Optional,
    Protocol,
    Type,
    TypeVar,
    runtime_checkable,
)

from fastapi import FastAPI
from injector import ScopeDecorator
from starlette.middleware import _MiddlewareFactory

T = TypeVar("T")


@runtime_checkable
class AppManagerProtocol(Protocol):
    """
    Protocol for the application manager contract.

    This protocol defines the contract for managing application-wide services,
    dependency injection, and server instance access. It is intended to be
    implemented by classes that coordinate the FastAPI application's lifecycle
    and dependency management.

    Methods:
        get_server(): Return the server protocol instance.
        get_instance(cls): Retrieve an instance of the given class from the injector.
        get_injector(): Return the underlying injector instance.
        register_singleton(cls, instance): Register a singleton instance for a class.
        register_provider(cls, provider, scope): Register a provider for a class with a given scope.

    Example:
        class MyAppManager(AppManagerProtocol):
            ...
        app_manager = MyAppManager()
        server = app_manager.get_server()
    """

    def setup_server(self, controllers: List[Any]) -> "ServerProtocol": ...
    def get_instance(self, cls: Type[T]) -> T: ...
    def get_injector(self) -> Any: ...
    def register_singleton(self, cls: Type[T], instance: T) -> None: ...
    def register_provider(
        self, cls: Type[T], provider: Any, scope: ScopeDecorator = ...
    ) -> None: ...


@runtime_checkable
class ServerProtocol(Protocol):
    """
    Protocol for the server contract.

    This protocol defines the contract for configuring and running the FastAPI server,
    including middleware, CORS, multi-tenancy, startup/shutdown hooks, and API setup.
    It is intended to be implemented by classes that encapsulate server configuration
    and lifecycle management.

    Methods:
        on_startup(func): Register a startup event handler.
        on_shutdown(func): Register a shutdown event handler.
        enable_tenant(): Enable multi-tenant support.
        enable_trusted_host(trusted_hosts, www_redirect): Enable trusted host validation.
        enable_simple_trace(trace_logger): Enable simple request tracing middleware.
        enable_etag(max_content_length): Enable ETag middleware.
        enable_hsts(): Enable HSTS middleware.
        force_https(): Force HTTPS redirection.
        disable_gzip(): Disable gzip compression.
        enable_cors(...): Enable and configure CORS middleware.
        add_middleware(middleware_class, **kwargs): Add custom middleware.
        setup_api(controllers, **kwargs): Register API controllers and setup routes.
        run(app): Run the FastAPI application.

    Example:
        class MyServer(ServerProtocol):
            ...
        server = MyServer()
        server.enable_cors(allow_origins=["*"])
        server.run(app)
    """

    def on_startup(
        self, func: Optional[Callable[[FastAPI, Any], Awaitable[None]]] = None
    ) -> "ServerProtocol": ...
    def on_shutdown(
        self, func: Optional[Callable[[FastAPI, Any], Awaitable[None]]] = None
    ) -> "ServerProtocol": ...
    def enable_tenant(self) -> "ServerProtocol": ...
    def enable_trusted_host(
        self, trusted_hosts: List[str] = ["*"], www_redirect: bool = True
    ) -> "ServerProtocol": ...
    def enable_simple_trace(self, trace_logger: Optional[Logger] = None) -> "ServerProtocol": ...
    def enable_etag(self, max_content_length: int = 1024 * 1024) -> "ServerProtocol": ...
    def enable_hsts(self) -> "ServerProtocol": ...
    def force_https(self) -> "ServerProtocol": ...
    def disable_gzip(self) -> "ServerProtocol": ...
    def enable_cors(
        self,
        *,
        allow_credentials: bool = True,
        allow_origins: List[str] = ["*"],
        allow_methods: List[str] = ["*"],
        allow_headers: List[str] = ["*"],
    ) -> "ServerProtocol": ...
    def add_middleware(
        self, middleware_class: _MiddlewareFactory, **kwargs: Any
    ) -> "ServerProtocol": ...
    def setup_api(self, controllers: List[Any], **kwargs) -> FastAPI: ...
    def get_app(self) -> FastAPI: ...
    def run(self, app: FastAPI): ...
