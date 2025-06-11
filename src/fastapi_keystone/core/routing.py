"""
Routing utilities for FastAPI-Keystone.

Provides decorator factories, route grouping, and controller registration helpers for FastAPI applications.
"""

import inspect
from enum import Enum
from functools import partial, wraps
from typing import Annotated, Any, Callable, Dict, List, Optional, Sequence, Type, Union

from fastapi import APIRouter, FastAPI, params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.types import IncEx
from fastapi.utils import generate_unique_id
from pydantic import BaseModel, ConfigDict
from starlette.middleware import Middleware
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from typing_extensions import Doc

from fastapi_keystone.core.contracts import AppManagerProtocol


class RouteConfig(BaseModel):
    """
    Route configuration for FastAPI decorator overlays.

    Mirrors FastAPI's APIRoute parameters for unified route definition.
    """

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)
    response_model: Annotated[
        Any,
        Doc(
            """
                The type to use for the response.

                It could be any valid Pydantic *field* type. So, it doesn't have to
                be a Pydantic model, it could be other things, like a `list`, `dict`,
                etc.

                It will be used for:

                * Documentation: the generated OpenAPI (and the UI at `/docs`) will
                    show it as the response (JSON Schema).
                * Serialization: you could return an arbitrary object and the
                    `response_model` would be used to serialize that object into the
                    corresponding JSON.
                * Filtering: the JSON sent to the client will only contain the data
                    (fields) defined in the `response_model`. If you returned an object
                    that contains an attribute `password` but the `response_model` does
                    not include that field, the JSON sent to the client would not have
                    that `password`.
                * Validation: whatever you return will be serialized with the
                    `response_model`, converting any data as necessary to generate the
                    corresponding JSON. But if the data in the object returned is not
                    valid, that would mean a violation of the contract with the client,
                    so it's an error from the API developer. So, FastAPI will raise an
                    error and return a 500 error code (Internal Server Error).

                Read more about it in the
                [FastAPI docs for Response Model](https://fastapi.tiangolo.com/tutorial/response-model/).
                """
        ),
    ] = Default(None)
    status_code: Annotated[
        Optional[int],
        Doc(
            """
                The default status code to be used for the response.

                You could override the status code by returning a response directly.

                Read more about it in the
                [FastAPI docs for Response Status Code](https://fastapi.tiangolo.com/tutorial/response-status-code/).
                """
        ),
    ] = None
    tags: Annotated[
        Optional[List[Union[str, Enum]]],
        Doc(
            """
                A list of tags to be applied to the *path operation*.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/#tags).
                """
        ),
    ] = None
    summary: Annotated[
        Optional[str],
        Doc(
            """
                A summary for the *path operation*.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
        ),
    ] = None
    description: Annotated[
        Optional[str],
        Doc(
            """
                A description for the *path operation*.

                If not provided, it will be extracted automatically from the docstring
                of the *path operation function*.

                It can contain Markdown.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Path Operation Configuration](https://fastapi.tiangolo.com/tutorial/path-operation-configuration/).
                """
        ),
    ] = None
    response_description: Annotated[
        str,
        Doc(
            """
                The description for the default response.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
        ),
    ] = "Successful Response"
    responses: Annotated[
        Optional[Dict[Union[int, str], Dict[str, Any]]],
        Doc(
            """
                Additional responses that could be returned by this *path operation*.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
        ),
    ] = None
    deprecated: Annotated[
        Optional[bool],
        Doc(
            """
                Mark this *path operation* as deprecated.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).
                """
        ),
    ] = None
    operation_id: Annotated[
        Optional[str],
        Doc(
            """
                Custom operation ID to be used by this *path operation*.

                By default, it is generated automatically.

                If you provide a custom operation ID, you need to make sure it is
                unique for the whole API.

                You can customize the
                operation ID generation with the parameter
                `generate_unique_id_function` in the `FastAPI` class.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
                """
        ),
    ] = None
    response_model_include: Annotated[
        Optional[IncEx],
        Doc(
            """
                Configuration passed to Pydantic to include only certain fields in the
                response data.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#response_model_include-and-response_model_exclude).
                """
        ),
    ] = None
    response_model_exclude: Annotated[
        Optional[IncEx],
        Doc(
            """
                Configuration passed to Pydantic to exclude certain fields in the
                response data.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#response_model_include-and-response_model_exclude).
                """
        ),
    ] = None
    response_model_by_alias: Annotated[
        bool,
        Doc(
            """
                Configuration passed to Pydantic to define if the response model
                should be serialized by alias when an alias is used.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#response_model_include-and-response_model_exclude).
                """
        ),
    ] = True
    response_model_exclude_unset: Annotated[
        bool,
        Doc(
            """
                Configuration passed to Pydantic to define if the response data
                should have all the fields, including the ones that were not set and
                have their default values. This is different from
                `response_model_exclude_defaults` in that if the fields are set,
                they will be included in the response, even if the value is the same
                as the default.

                When `True`, default values are omitted from the response.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#use-the-response_model_exclude_unset-parameter).
                """
        ),
    ] = False
    response_model_exclude_defaults: Annotated[
        bool,
        Doc(
            """
                Configuration passed to Pydantic to define if the response data
                should have all the fields, including the ones that have the same value
                as the default. This is different from `response_model_exclude_unset`
                in that if the fields are set but contain the same default values,
                they will be excluded from the response.

                When `True`, default values are omitted from the response.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#use-the-response_model_exclude_unset-parameter).
                """
        ),
    ] = False
    response_model_exclude_none: Annotated[
        bool,
        Doc(
            """
                Configuration passed to Pydantic to define if the response data should
                exclude fields set to `None`.

                This is much simpler (less smart) than `response_model_exclude_unset`
                and `response_model_exclude_defaults`. You probably want to use one of
                those two instead of this one, as those allow returning `None` values
                when it makes sense.

                Read more about it in the
                [FastAPI docs for Response Model - Return Type](https://fastapi.tiangolo.com/tutorial/response-model/#response_model_exclude_none).
                """
        ),
    ] = False
    include_in_schema: Annotated[
        bool,
        Doc(
            """
                Include this *path operation* in the generated OpenAPI schema.

                This affects the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for Query Parameters and String Validations](https://fastapi.tiangolo.com/tutorial/query-params-str-validations/#exclude-from-openapi).
                """
        ),
    ] = True
    response_class: Annotated[
        Type[Response],
        Doc(
            """
                Response class to be used for this *path operation*.

                This will not be used if you return a response directly.

                Read more about it in the
                [FastAPI docs for Custom Response - HTML, Stream, File, others](https://fastapi.tiangolo.com/advanced/custom-response/#redirectresponse).
                """
        ),
    ] = Default(JSONResponse)
    name: Annotated[
        Optional[str],
        Doc(
            """
                Name for this *path operation*. Only used internally.
                """
        ),
    ] = None
    openapi_extra: Annotated[
        Optional[Dict[str, Any]],
        Doc(
            """
                Extra metadata to be included in the OpenAPI schema for this *path
                operation*.

                Read more about it in the
                [FastAPI docs for Path Operation Advanced Configuration](https://fastapi.tiangolo.com/advanced/path-operation-advanced-configuration/#custom-openapi-path-operation-schema).
                """
        ),
    ] = None
    callbacks: Annotated[
        Optional[List[BaseRoute]],
        Doc(
            """
                List of *path operations* that will be used as OpenAPI callbacks.

                This is only for OpenAPI documentation, the callbacks won't be used
                directly.

                It will be added to the generated OpenAPI (e.g. visible at `/docs`).

                Read more about it in the
                [FastAPI docs for OpenAPI Callbacks](https://fastapi.tiangolo.com/advanced/openapi-callbacks/).
                """
        ),
    ] = None
    generate_unique_id_function: Annotated[
        Callable[[APIRoute], str],
        Doc(
            """
                Customize the function used to generate unique IDs for the *path
                operations* shown in the generated OpenAPI.

                This is particularly useful when automatically generating clients or
                SDKs for your API.

                Read more about it in the
                [FastAPI docs about how to Generate Clients](https://fastapi.tiangolo.com/advanced/generate-clients/#custom-generate-unique-id-function).
                """
        ),
    ] = Default(generate_unique_id)
    middlewares: Optional[List[Callable]] = None  # 你的自定义参数


class Router:
    """
    Simple router class for creating get, post, put, delete, etc. decorator factories.
    """

    def get(
        self,
        path: Annotated[str, Doc("The URL path to be used for this *path operation*.")],
        *,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ):
        """
        Create a GET route decorator.

        Args:
            path (str): The URL path for the route.
            dependencies (Optional[Sequence[params.Depends]]): Dependencies for the route.
            config (Optional[RouteConfig]): Additional route config.

        Returns:
            Callable: The decorator function.
        """
        return self._create_decorator(path, "GET", dependencies, config)

    def post(
        self,
        path: Annotated[str, Doc("The URL path to be used for this *path operation*.")],
        *,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ):
        return self._create_decorator(path, "POST", dependencies, config)

    def patch(
        self,
        path: Annotated[str, Doc("The URL path to be used for this *path operation*.")],
        *,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ):
        return self._create_decorator(path, "PATCH", dependencies, config)

    def delete(
        self,
        path: Annotated[str, Doc("The URL path to be used for this *path operation*.")],
        *,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ):
        return self._create_decorator(path, "DELETE", dependencies, config)

    def put(
        self,
        path: Annotated[str, Doc("The URL path to be used for this *path operation*.")],
        *,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ):
        return self._create_decorator(path, "PUT", dependencies, config)

    def __getattr__(self, method: Annotated[str, Doc("HTTP method")]) -> Callable:
        allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
        if method.upper() not in allowed_methods:
            raise ValueError(
                f"Invalid HTTP method: {method}. Allowed methods are: {', '.join(allowed_methods)}"
            )
        # e.g., router.get -> partial(self._create_decorator, method="GET")
        partial_func = partial(self._create_decorator, method=method.upper())

        @wraps(self._create_decorator)
        def endpoint(*args, **kwargs):
            return partial_func(*args, **kwargs)

        return endpoint

    def _create_decorator(
        self,
        path: Annotated[
            str,
            Doc(
                """
                The URL path to be used for this *path operation*.

                For example, in `http://example.com/items`, the path is `/items`.
                """
            ),
        ],
        method: str,
        dependencies: Annotated[
            Optional[Sequence[params.Depends]],
            Doc(
                """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.

                Read more about it in the
                [FastAPI docs for Dependencies in path operation decorators](https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-in-path-operation-decorators/).
                """
            ),
        ] = None,
        config: Optional[RouteConfig] = None,
    ) -> Callable:
        """
        Internal helper to create a route decorator.

        Args:
            path (str): The URL path.
            method (str): HTTP method.
            dependencies (Optional[Sequence[params.Depends]]): Dependencies.
            config (Optional[RouteConfig]): Route config.

        Returns:
            Callable: The decorator function.
        """

        def decorator(func: Callable) -> Callable:
            # 将路由信息附加到函数对象上，以便后续统一注册
            if not hasattr(func, "_route_info"):
                setattr(func, "_route_info", {})
            getattr(func, "_route_info", {}).update(
                {
                    "path": path,
                    "methods": [method],
                    "dependencies": dependencies,
                }
            )
            if config:
                getattr(func, "_route_info", {}).update(
                    config.model_dump(exclude_none=True)
                )
            return func

        return decorator


router = Router()


def group(
    prefix: Annotated[str, Doc("路由组前缀")],
    dependencies: Annotated[
        Optional[Sequence[params.Depends]],
        Doc(
            """
                A list of dependencies (using `Depends()`) to be applied to the
                *path operation*.
                """
        ),
    ] = None,
):
    """
    Class decorator for defining route group prefix and dependencies.

    Args:
        prefix (str): Route group prefix.
        dependencies (Optional[Sequence[params.Depends]]): Group dependencies.

    Returns:
        Callable: The class decorator.
    """

    def decorator(cls):
        # 将组信息附加到类对象上
        cls._group_info = {
            "prefix": prefix,
            "dependencies": dependencies or [],
        }
        return cls

    return decorator


def RoutingMiddlewareWrapper(
    middleware: Optional[List[Middleware]] = None,
) -> Type[APIRoute]:
    """
    Wrapper to apply middleware to FastAPI routes.

    Args:
        middleware (Optional[List[Middleware]]): List of middleware tuples.

    Returns:
        Type[APIRoute]: Custom APIRoute class with middleware applied.
    """

    class WithMiddlewareAPIRoute(APIRoute):
        def __init__(self, *args, **kwargs) -> None:
            super().__init__(*args, **kwargs)
            app = self.app
            for cls, args, kwargs in reversed(middleware or []):
                app = cls(app, *args, **kwargs)
            self.app = app

    return WithMiddlewareAPIRoute


def bind_method_to_instance(method, instance):
    """
    Bind a method to an instance, removing 'self' from the signature for FastAPI.

    Args:
        method (Callable): The method to bind.
        instance (Any): The instance to bind to.

    Returns:
        Callable: The bound method.
    """
    sig = inspect.signature(method)
    params = list(sig.parameters.values())
    # 移除第一个参数（self）
    new_params = params[1:]
    new_sig = sig.replace(parameters=new_params)

    @wraps(method)
    def wrapper(*args, **kwargs):
        return method(instance, *args, **kwargs)

    setattr(wrapper, "__signature__", new_sig)  # 让 FastAPI 看到没有 self 的签名
    setattr(wrapper, "__annotations__", method.__annotations__)
    setattr(wrapper, "__doc__", method.__doc__)
    return wrapper


def register_controllers(
    app: FastAPI, manager: AppManagerProtocol, controllers: List[Any]
):
    """
    Discover and register routes from controller classes.

    Args:
        app (FastAPI): The FastAPI app instance.
        manager (AppManagerProtocol): The DI manager.
        controllers (List[Any]): List of controller classes.
    """
    for controller_class in controllers:
        # 使用 DI 容器实例化控制器
        controller_instance = manager.get_instance(controller_class)

        group_info: Dict[str, Any] = getattr(controller_class, "_group_info", {})
        group_prefix: str = group_info.get("prefix", "") or ""
        group_deps: Sequence[params.Depends] = group_info.get("dependencies", []) or []

        # 遍历类的所有成员
        for _, method in inspect.getmembers(controller_class, inspect.isfunction):
            if not hasattr(method, "_route_info"):
                continue

            route_info: Dict[str, Any] = getattr(method, "_route_info")
            # 合并组和方法的路由信息
            # 确保前缀不以/结尾，路径以/开头
            group_prefix = group_prefix.rstrip("/")
            route_path = route_info["path"].lstrip("/")
            full_path = f"{group_prefix}/{route_path}" if route_path else group_prefix

            # 中间件叠加
            all_deps: Optional[Sequence[params.Depends]] = None
            route_deps = route_info.get("dependencies", []) or []
            if len(group_deps) > 0:
                all_deps = list(group_deps) + list(route_deps)
            elif len(route_deps) > 0:
                all_deps = route_deps

            # 将控制器方法绑定到实例
            endpoint = bind_method_to_instance(method, controller_instance)
            # 更新函数签名以帮助 FastAPI 生成正确的 OpenAPI 文档
            # Now endpoint has __name__, __annotations__, etc.

            # 动态创建 APIRouter 来处理前缀和依赖
            # 这样更符合FastAPI的习惯，并能更好地利用其特性
            router_instance = APIRouter(prefix=group_prefix, dependencies=group_deps)
            route_config = route_info.get("config", {}) or {}
            router_instance.add_api_route(
                path=route_info["path"],
                endpoint=endpoint,
                methods=route_info["methods"],
                dependencies=all_deps,
                # ... 其他路由参数，如 response_model
                **route_config,
            )

            app.include_router(router_instance)
            print(f"Registered route: {route_info['methods']} {full_path}")
