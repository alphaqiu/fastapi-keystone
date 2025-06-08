"""
FastAPI Keystone 代码文档示例

本文件展示如何在代码文档字符串（docstring）中包含使用示例。
这是除了独立examples目录外的另一种提供示例的方式。
"""

from typing import List, Optional

from injector import inject

from fastapi_keystone.core.response import APIResponse
from fastapi_keystone.core.routing import Router, group


class UserService:
    """用户服务类

    提供用户管理的核心业务逻辑，包括用户的创建、查询、更新和删除。

    Examples:
        基本用法：

        >>> user_service = UserService()
        >>> user = user_service.create_user("张三", "zhangsan@example.com")
        >>> print(user["name"])
        '张三'

        查询用户：

        >>> user = user_service.get_user_by_id(1)
        >>> if user:
        ...     print(f"用户：{user['name']}")
        用户：张三

        批量查询：

        >>> users = user_service.get_users()
        >>> len(users) > 0
        True
    """

    def __init__(self):
        self._users = {}
        self._next_id = 1

    def create_user(self, name: str, email: str, age: Optional[int] = None) -> dict:
        """创建新用户

        Args:
            name: 用户姓名
            email: 用户邮箱
            age: 用户年龄（可选）

        Returns:
            创建的用户信息字典

        Examples:
            创建基本用户：

            >>> service = UserService()
            >>> user = service.create_user("李四", "lisi@example.com")
            >>> user["name"]
            '李四'
            >>> user["email"]
            'lisi@example.com'

            创建包含年龄的用户：

            >>> user = service.create_user("王五", "wangwu@example.com", 25)
            >>> user["age"]
            25
        """
        user = {
            "id": self._next_id,
            "name": name,
            "email": email,
            "age": age,
            "created_at": "2024-01-01T00:00:00Z",
        }
        self._users[self._next_id] = user
        self._next_id += 1
        return user

    def get_user_by_id(self, user_id: int) -> Optional[dict]:
        """根据ID获取用户

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典，如果不存在则返回None

        Examples:
            获取存在的用户：

            >>> service = UserService()
            >>> user = service.create_user("测试用户", "test@example.com")
            >>> found_user = service.get_user_by_id(user["id"])
            >>> found_user["name"]
            '测试用户'

            获取不存在的用户：

            >>> not_found = service.get_user_by_id(999)
            >>> not_found is None
            True
        """
        return self._users.get(user_id)

    def get_users(self, limit: Optional[int] = None) -> List[dict]:
        """获取用户列表

        Args:
            limit: 限制返回数量（可选）

        Returns:
            用户列表

        Examples:
            获取所有用户：

            >>> service = UserService()
            >>> service.create_user("用户1", "user1@example.com")
            {'id': 1, 'name': '用户1', 'email': 'user1@example.com', 'age': None, 'created_at': '2024-01-01T00:00:00Z'}
            >>> service.create_user("用户2", "user2@example.com")
            {'id': 2, 'name': '用户2', 'email': 'user2@example.com', 'age': None, 'created_at': '2024-01-01T00:00:00Z'}
            >>> users = service.get_users()
            >>> len(users)
            2

            限制返回数量：

            >>> users = service.get_users(limit=1)
            >>> len(users)
            1
        """
        all_users = list(self._users.values())
        if limit:
            return all_users[:limit]
        return all_users


# 创建路由器实例
router = Router()


@group("/api/v1/users")
class UserController:
    """用户控制器

    提供用户管理的HTTP API接口。所有API都返回标准化的APIResponse格式。

    Examples:
        在FastAPI应用中使用：

        >>> from fastapi import FastAPI
        >>> from fastapi_keystone import Server, Config
        >>> from fastapi_keystone.core.routing import register_controllers
        >>> from injector import Injector
        >>>
        >>> app = FastAPI()
        >>> injector = Injector()
        >>> register_controllers(app, injector, [UserController])

        这将注册以下路由：
        - GET /api/v1/users - 获取用户列表
        - GET /api/v1/users/{user_id} - 获取指定用户
        - POST /api/v1/users - 创建新用户
        - PUT /api/v1/users/{user_id} - 更新用户
        - DELETE /api/v1/users/{user_id} - 删除用户
    """

    @inject
    def __init__(self, user_service: UserService):
        """初始化用户控制器

        Args:
            user_service: 用户服务实例（通过依赖注入）

        Examples:
            手动创建（不推荐，应使用依赖注入）：

            >>> service = UserService()
            >>> controller = UserController(service)
        """
        self.user_service = user_service

    @router.get("/")
    async def list_users(self, limit: Optional[int] = None) -> APIResponse[List[dict]]:
        """获取用户列表

        Args:
            limit: 限制返回数量（查询参数）

        Returns:
            包含用户列表的标准API响应

        Examples:
            成功响应格式：

            {
                "success": true,
                "message": "操作成功",
                "data": [
                    {
                        "id": 1,
                        "name": "张三",
                        "email": "zhangsan@example.com",
                        "age": 25,
                        "created_at": "2024-01-01T00:00:00Z"
                    }
                ],
                "code": 200,
                "timestamp": "2024-01-01T00:00:00Z"
            }

            使用curl测试：

            $ curl "http://localhost:8000/api/v1/users"
            $ curl "http://localhost:8000/api/v1/users?limit=10"
        """
        users = self.user_service.get_users(limit)
        return APIResponse.success(users)

    @router.get("/{user_id}")
    async def get_user(self, user_id: int) -> APIResponse[dict]:
        """获取指定用户

        Args:
            user_id: 用户ID（路径参数）

        Returns:
            包含用户信息的标准API响应

        Raises:
            404: 用户不存在

        Examples:
            成功响应：

            {
                "success": true,
                "message": "操作成功",
                "data": {
                    "id": 1,
                    "name": "张三",
                    "email": "zhangsan@example.com",
                    "age": 25,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                "code": 200,
                "timestamp": "2024-01-01T00:00:00Z"
            }

            用户不存在时的响应：

            {
                "success": false,
                "message": "用户不存在",
                "data": null,
                "code": 404,
                "timestamp": "2024-01-01T00:00:00Z"
            }

            使用curl测试：

            $ curl "http://localhost:8000/api/v1/users/1"
        """
        user = self.user_service.get_user_by_id(user_id)
        if not user:
            return APIResponse.error("用户不存在", code=404)
        return APIResponse.success(user)

    @router.post("/")
    async def create_user(self, user_data: dict) -> APIResponse[dict]:
        """创建新用户
        
        Args:
            user_data: 用户数据（请求体）
                - name (str): 用户姓名
                - email (str): 用户邮箱
                - age (int, optional): 用户年龄
                
        Returns:
            包含创建用户信息的标准API响应
            
        Examples:
            请求示例：
            
            POST /api/v1/users
            Content-Type: application/json
            
            {
                "name": "新用户",
                "email": "newuser@example.com",
                "age": 30
            }
            
            成功响应：
            
            {
                "success": true,
                "message": "用户创建成功",
                "data": {
                    "id": 2,
                    "name": "新用户",
                    "email": "newuser@example.com",
                    "age": 30,
                    "created_at": "2024-01-01T00:00:00Z"
                },
                "code": 201,
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            使用curl测试：
            
            $ curl -X POST "http://localhost:8000/api/v1/users" \\
                   -H "Content-Type: application/json" \\
                   -d '{"name": "测试用户", "email": "test@example.com", "age": 25}'
        """
        user = self.user_service.create_user(
            name=user_data["name"], email=user_data["email"], age=user_data.get("age")
        )
        return APIResponse.success(user, message="用户创建成功", code=201)


def demonstrate_docstring_examples():
    """演示函数，展示如何在文档中提供完整的使用示例

    Examples:
        完整的应用设置和使用：

        >>> from fastapi import FastAPI
        >>> from fastapi_keystone import Server, Config
        >>> from fastapi_keystone.core.routing import register_controllers
        >>> from injector import Injector, Module, provider, singleton
        >>> import uvicorn
        >>>
        >>> # 创建依赖注入模块
        >>> class ServiceModule(Module):
        ...     @provider
        ...     @singleton
        ...     def user_service(self) -> UserService:
        ...         return UserService()
        >>>
        >>> # 设置应用
        >>> config = Config()
        >>> server = Server(config)
        >>> injector = Injector([ServiceModule()])
        >>>
        >>> # 注册控制器
        >>> register_controllers(server.app, injector, [UserController])
        >>>
        >>> # 启动服务器
        >>> if __name__ == "__main__":
        ...     uvicorn.run(server.app, host="0.0.0.0", port=8000)

        这种方式的优点：
        1. 代码和文档紧密结合
        2. 容易保持同步
        3. IDE可以直接显示
        4. 支持doctest自动测试

        缺点：
        1. 文档字符串可能过长
        2. 复杂示例难以在docstring中展示
        3. 不利于独立运行和测试
    """
    pass


if __name__ == "__main__":
    # 可以运行doctest来验证文档中的示例
    import doctest

    doctest.testmod(verbose=True)
