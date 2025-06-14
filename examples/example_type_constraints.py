#!/usr/bin/env python3
"""
APIResponse 类型约束示例

演示如何使用 APIResponse 的类型约束功能
"""

from typing import List

from pydantic import BaseModel

from src.fastapi_keystone.core.response import APIResponse, APIResponseModel


# 定义示例 BaseModel
class User(BaseModel):
    id: int
    name: str
    email: str


class Product(BaseModel):
    id: int
    title: str
    price: float


def main():
    print("=== APIResponse 类型约束示例 ===\n")

    # 1. JSON 基本类型
    print("1. JSON 基本类型:")

    # 字符串
    response1 = APIResponse.success(data="Hello World")
    print(f"字符串: {response1.model_dump_json()}")

    # 数字
    response2 = APIResponse.success(data=42)
    print(f"数字: {response2.model_dump_json()}")

    # 字典
    response3 = APIResponse.success(data={"key": "value", "count": 10})
    print(f"字典: {response3.model_dump_json()}")

    # 列表
    response4 = APIResponse.success(data=[1, 2, 3, "hello", True])
    print(f"列表: {response4.model_dump_json()}")

    print()

    # 2. BaseModel 类型
    print("2. BaseModel 类型:")

    user = User(id=1, name="Alice", email="alice@example.com")
    response5 = APIResponse.success(data=user)
    print(f"BaseModel: {response5.model_dump_json()}")

    print()

    # 3. BaseModel 列表类型
    print("3. BaseModel 列表类型:")

    users = [
        User(id=1, name="Alice", email="alice@example.com"),
        User(id=2, name="Bob", email="bob@example.com"),
    ]
    response6 = APIResponse.success(data=users)
    print(f"BaseModel 列表: {response6.model_dump_json()}")

    print()

    # 4. APIResponseModel 示例
    print("4. APIResponseModel 示例:")

    # 字符串类型
    model1 = APIResponseModel[str](code=200, message="success", data="Hello")
    print(f"APIResponseModel[str]: {model1.model_dump()}")

    # BaseModel 类型
    model2 = APIResponseModel[User](code=200, message="success", data=user)
    print(f"APIResponseModel[User]: {model2.model_dump()}")

    # BaseModel 列表类型
    model3 = APIResponseModel[List[User]](code=200, message="success", data=users)
    print(f"APIResponseModel[List[User]]: {model3.model_dump()}")

    print()

    # 5. 分页响应示例
    print("5. 分页响应示例:")

    products = [
        Product(id=1, title="Laptop", price=999.99),
        Product(id=2, title="Mouse", price=29.99),
    ]

    paginated_response = APIResponse.paginated(data=products, total=100, page=1, size=2)
    print(f"分页响应: {paginated_response.model_dump_json()}")
    print(f"model_dump(): {paginated_response.model_dump()}")

    print("\n=== 类型约束验证完成 ===")


if __name__ == "__main__":
    main()
