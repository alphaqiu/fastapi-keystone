# fastapi-keystone 项目开发规则（cursorrules）

## 1. 项目概述
- **fastapi-keystone** 是基于 FastAPI 的快速开发框架 SDK 项目
- 采用契约优先、模式驱动的开发方式
- 支持多租户、依赖注入、异步处理等企业级特性
- 发布到 PyPI，供其他项目引用

## 2. 目录结构与包布局
```
fastapi-keystone/
├── src/
│   └── fastapi_keystone/          # 主包（注意下划线）
│       ├── __init__.py
│       ├── config/               # 配置管理
│       │   ├── __init__.py
│       │   └── config.py        # 配置加载与管理
│       ├── core/                 # 核心组件
│       │   ├── __init__.py
│       │   ├── app.py           # AppManager 应用管理器
│       │   ├── server.py        # FastAPI 服务器
│       │   ├── routing.py       # 路由管理
│       │   ├── exceptions.py    # 异常处理
│       │   ├── response.py      # 响应封装
│       │   ├── request.py       # 请求模型
│       │   ├── middlewares.py   # 中间件
│       │   ├── contracts.py     # 协议定义
│       │   ├── pagination.py    # 分页查询
│       │   ├── logger.py        # 日志配置
│       │   └── db.py           # 数据库连接
│       ├── common/              # 通用工具
│       │   ├── __init__.py
│       │   ├── singleton.py     # 单例模式实现
│       │   └── dicts.py        # 字典工具
│       └── caches/              # 缓存相关（预留）
├── tests/                       # 测试代码（与 src 同级）
├── examples/                    # 示例代码
│   ├── basic/                  # 基础示例
│   │   ├── hello-world/       # Hello World 示例
│   │   └── singleton-di/      # 依赖注入示例
│   ├── intermediate/          # 中级示例
│   │   ├── config-extension/  # 配置扩展示例
│   │   └── crud-api/         # CRUD API 示例
│   └── advanced/             # 高级示例
│       └── lock-comparison/  # 锁机制对比示例
├── docs/                        # 项目文档
├── pyproject.toml               # 项目配置
├── MANIFEST.in                  # 打包清单
├── LICENSE                      # MIT 许可证
├── README.md                    # 项目说明
├── config.example.json          # 配置示例
├── config.example.yaml          # YAML 配置示例（内容需与 JSON 保持一致）
├── main.py                      # 入口文件（示例）
├── VERSION                      # 版本号文件
├── Makefile                     # 构建脚本
├── CONTRIBUTING.md              # 贡献指南
└── SECURITY.md                  # 安全政策
```

**重要约定：**
- 包名使用 `fastapi_keystone`（下划线），项目名使用 `fastapi-keystone`（连字符）
- 所有业务代码位于 `src/fastapi_keystone/` 下
- 测试代码位于项目根目录的 `tests/`，与 `src/` 同级
- 示例代码位于 `examples/` 目录，按复杂度分层组织

## 3. 依赖与环境管理
- **Python 版本**：`>=3.10`（支持 3.10, 3.11, 3.12, 3.13）
- **包管理器**：`uv`（虚拟环境、依赖安装、构建、发布）
- **依赖配置**：使用 `pyproject.toml` 的 `[dependency-groups]` 分组管理
- **生产依赖**：
  - FastAPI、Pydantic、SQLAlchemy、injector（核心框架）
  - aiomysql、aiosqlite、asyncpg（数据库驱动）
  - redis、cachetools（缓存支持）
  - pyyaml、rich（配置与输出）
  - python-ulid（唯一标识符）
- **开发依赖**：pytest、black、ruff、bumpver、twine、mypy、isort 等

**常用命令：**
```bash
uv sync                    # 同步所有依赖
uv run pytest             # 运行测试
uv run pytest --cov=src   # 运行覆盖率测试
uv build                  # 构建包
uv run twine upload dist/* # 发布到 PyPI
uv pip install pyyaml     # 安装 YAML 支持
```

## 4. 配置管理
- **技术栈**：Pydantic v2 + pydantic-settings
- **配置加载**：支持 JSON 文件、YAML 文件（.json/.yaml/.yml）、环境变量、.env 文件
- **多租户支持**：`databases` 字段动态映射多数据库配置
- **配置模型**：
  - `Config`：主配置类（server、logger、databases）
  - `DatabasesConfig`：继承 `RootModel[Dict[str, DatabaseConfig]]`
  - `DatabaseConfig`：单个数据库配置
  - 必须包含 `default` 数据库配置
- **配置优先级**：传参 > 配置文件（json/yaml/yml）> 环境变量 > 默认值
- **配置文件格式**：
  - 推荐同时维护 `config.example.json` 和 `config.example.yaml`，内容保持一致
  - 文档、示例、测试均需给出 YAML/JSON 两种格式的用法

## 5. 代码规范与质量
- **代码风格**：遵循 PEP8、PEP484、PEP517、PEP621
- **格式化工具**：`black`
- **静态检查**：`ruff`（行长度限制：100字符）、`isort`、`mypy`
- **命名约定**：
  - 变量/函数：`snake_case`
  - 类名：`PascalCase`
  - 常量：`UPPER_SNAKE_CASE`
  - 文件/目录：`snake_case`
- **文档要求**：
  - 公共函数、类需添加 docstring
  - 复杂逻辑需有单行注释
  - 使用类型提示（Type Hints）
  - **注释风格**：本项目统一采用 Google 风格 docstring 进行注释，所有公共函数、类、方法的文档字符串需遵循 Google 风格（详见 https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings）。

## 6. 测试策略
- **测试框架**：pytest + pytest-asyncio + pytest-cov
- **测试目录**：`tests/`，测试文件以 `test_*.py` 命名
- **运行方式**：`uv run pytest`（项目根目录）
- **覆盖率测试**：`uv run pytest --cov=src --cov-report=html`
- **导入规范**：
  ```python
  from fastapi_keystone.config.config import Config
  from fastapi_keystone.core.server import Server
  from fastapi_keystone.core.app import AppManager
  ```
  所有生成的测试代码，统一都放到 tests/ 目录下，不要删除。
  
- **pytest 配置**：`pyproject.toml` 中设置 `pythonpath = ["src"]` 和 `asyncio_mode = "auto"`
- **测试规范补充**：
  - 所有关键配置加载测试需覆盖 JSON/YAML 两种格式，确保行为一致
  - 示例代码需演示两种格式的加载
  - 文档需明确说明支持的配置格式，并给出 YAML 示例片段

## 7. 架构设计
- **核心组件**：
  - `AppManager`：应用管理器，依赖注入容器的核心
  - `Server`：FastAPI 应用封装，支持生命周期管理
  - `Router`：路由装饰器，支持类级别路由定义
  - `APIException`：统一异常处理
  - `APIResponse`：标准化响应格式
  - `PageRequest`：分页请求模型
  - `PageQueryMixin`：分页查询混入类
- **依赖注入**：使用 `injector` 库实现 DI 容器，通过 `AppManager` 统一管理
- **中间件支持**：可扩展的中间件系统（CORS、GZIP、ETag、HSTS等）
- **异步优先**：全面支持 async/await
- **协议定义**：使用 `Protocol` 定义组件契约（`AppManagerProtocol`、`ServerProtocol`）

## 8. 版本管理与发布
- **版本管理工具**：`bumpver`
- **版本模式**：语义化版本号（MAJOR.MINOR.PATCH）
- **版本文件**：`VERSION` 文件存储当前版本号
- **版本递增**：
  ```bash
  bumpver update --patch  # 修订版本
  bumpver update --minor  # 次版本
  bumpver update --major  # 主版本
  ```
- **自动化**：bumpver 会同步更新 `pyproject.toml` 和 `VERSION` 文件
- **Git 集成**：自动 commit、tag、push

## 9. 打包与分发
- **构建标准**：PEP517/621 标准
- **打包工具**：`uv build`
- **打包控制**：
  - `MANIFEST.in`：控制 sdist 包含的文件
  - `tool.setuptools.packages.find`：控制 wheel 包含的包
  - 排除测试文件和缓存文件
- **分发平台**：PyPI
- **发布流程**：
  1. 更新版本：`bumpver update --patch`
  2. 构建包：`uv build`
  3. 发布：`uv run twine upload dist/*`

## 10. 调试与开发
- **IDE 配置**：`.vscode/` 目录包含 VSCode 配置
- **IDE 调试**：推荐使用 VSCode 测试资源管理器进行单步调试
- **日志记录**：使用 `rich` 库美化输出
- **开发服务器**：`uvicorn` 用于本地开发
- **构建工具**：`Makefile` 提供常用构建命令

## 11. 文档与示例
- **文档目录**：`docs/` 存放项目文档
- **配置示例**：`config.example.json`、`config.example.yaml` 提供配置模板，内容需保持一致
- **入口示例**：`main.py` 展示框架使用方式
- **示例项目**：`examples/` 目录包含分层的示例代码
  - `basic/`：基础示例（hello-world、singleton-di）
  - `intermediate/`：中级示例（config-extension、crud-api）
  - `advanced/`：高级示例（lock-comparison）
- **README**：包含安装、使用、贡献指南
- **YAML 配置片段**：文档和示例中需给出 YAML 配置片段

## 12. 许可证与开源
- **许可证**：MIT License
- **开源协议**：允许商业使用、修改、分发
- **版权信息**：包含在 `LICENSE` 文件中
- **贡献指南**：`CONTRIBUTING.md` 说明贡献流程
- **安全政策**：`SECURITY.md` 说明安全问题报告流程

---

## 开发工作流
1. **环境准备**：`uv sync` 安装依赖
2. **功能开发**：遵循契约优先、测试驱动
3. **代码检查**：`ruff check` + `black --check` + `mypy`
4. **运行测试**：`uv run pytest --cov=src`
5. **版本更新**：`bumpver update --patch`
6. **构建发布**：`uv build` + `uv run twine upload dist/*`
7. **配置相关变更**：
   - 新增/修改配置相关功能时，需同步更新 YAML/JSON 示例、文档、测试
   - 新增依赖需在 `pyproject.toml` 和文档中注明

## 特殊约定
- **AppManager 设计**：不是单例，每个实例有独立的依赖注入容器
- **服务单例范围**：服务只在同一个 AppManager 实例内是单例
- **示例维护**：示例代码需与主代码保持同步，定期更新
- **测试覆盖**：核心组件需要完整的单元测试覆盖

如有特殊约定或变更，请在本文件补充说明。 