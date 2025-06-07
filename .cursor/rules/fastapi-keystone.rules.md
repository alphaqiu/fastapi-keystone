# fastapi-keystone 项目开发规则（cursorrules）

## 1. 目录结构与包布局
- 采用 src 布局，主代码位于 `src/` 目录下。
- 配置相关代码位于 `src/config/`。
- 通用代码可放在 `src/common/`，核心业务逻辑建议放在 `src/core/`。
- 测试代码位于项目根目录下的 `tests/`，与 `src/` 同级。
- 配置文件如 `config.example.json` 放在项目根目录。

## 2. 依赖与环境
- 依赖管理采用 `pyproject.toml`，生产依赖和开发依赖分组管理。
- 推荐使用 `uv` 工具进行虚拟环境和依赖操作。
- Python 版本要求：`>=3.13`。

## 3. 配置管理
- 配置采用 Pydantic v2 + pydantic-settings 实现，所有配置项均有类型注解。
- 支持多数据库（多租户）配置，`databases` 字段为动态映射，必须包含 `default` 键。
- 配置加载支持 JSON 文件、环境变量、.env 文件，优先级为：传参 > 配置文件 > 环境变量。
- 配置模型示例：
  - `Config` 主配置类，包含 `server`、`logger`、`databases` 等字段。
  - `DatabasesConfig` 继承自 `RootModel[Dict[str, DatabaseConfig]]`，动态支持多数据库。

## 4. 代码风格与规范
- 遵循 PEP8、PEP484、PEP517、PEP621。
- 代码格式化工具：`black`。
- 代码静态检查工具：`ruff`、`isort`。
- 变量、函数、类命名规范：
  - 变量/函数：snake_case
  - 类名：PascalCase
  - 常量：UPPER_SNAKE_CASE
- 公共函数、类需添加 docstring，复杂逻辑需有单行注释。
- 推荐使用类型提示（Type Hints）。

## 5. 测试
- 测试框架：pytest，异步测试用 pytest-asyncio。
- 测试目录为 `tests/`，测试文件以 `test_*.py` 命名。
- 测试用例导入主包时，使用 `from config.config import ...`，并确保 `PYTHONPATH=src`。
- 推荐在项目根目录下运行 `uv run pytest`。
- 配置 `pyproject.toml` 的 pytest 选项，`pythonpath = ["src"]`。

## 6. 打包与分发
- 打包采用 PEP517/621 标准，配置在 `pyproject.toml`。
- 仅 `src/` 下的包会被打包，`tests/` 不会被包含。
- 发布前请确保所有依赖、配置、文档齐全。

## 7. 其他约定
- 配置、代码、文档需保持同步，变更需及时更新文档。
- 代码生成、模式驱动优先，减少手写样板代码。
- 所有包内导入使用绝对导入。
- 项目内如需添加新模块，建议先定义模式（schema），再生成实现。

---

如有特殊约定或变更，请在本文件补充说明。 