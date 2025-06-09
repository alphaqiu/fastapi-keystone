# Contributing to fastapi-keystone

感谢你对 fastapi-keystone 的关注和贡献！我们欢迎所有形式的贡献，包括代码、文档、测试、issue 反馈等。

## 如何参与贡献

1. **Fork 本仓库** 到你的 GitHub 账号
2. **新建分支**（建议使用 `feature/xxx`、`fix/xxx`、`docs/xxx` 等命名）
3. **开发与测试**，确保本地所有测试通过
4. **提交 Pull Request** 到主仓库的 `main` 分支
5. 等待 Maintainer 审核与合并

## Issue 反馈
- 欢迎通过 [GitHub Issues](https://github.com/alpha-keystone/fastapi-keystone/issues) 提交 bug、建议、需求等
- 请尽量提供详细的描述、重现步骤、环境信息、截图/日志等

## 代码规范
- 遵循 [PEP8](https://peps.python.org/pep-0008/) 代码风格
- 强制类型提示（Type Hints）
- 公共函数/类需添加 docstring
- 复杂逻辑需有单行注释
- 变量/函数：`snake_case`，类名：`PascalCase`，常量：`UPPER_SNAKE_CASE`
- 使用 `black` 自动格式化，`ruff`/`isort` 静态检查
- 依赖管理统一用 `uv`，不要直接用 `pip`

## 测试要求
- 所有新功能/修复必须有对应的单元测试（`tests/` 目录，`test_*.py` 文件）
- 测试需覆盖 JSON/YAML 配置加载场景
- 推荐使用 `pytest`、`pytest-asyncio`、`pytest-cov`
- 本地运行：
  ```bash
  uv run pytest
  uv run pytest --cov=src
  ```

## 文档要求
- 重要变更需同步更新 `README.md`、`docs/`、示例代码
- 配置相关需同时维护 `config.example.json` 和 `config.example.yaml`
- 文档和示例中需给出 YAML 配置片段

## 依赖与环境
- Python >= 3.13
- 依赖管理：
  ```bash
  uv sync
  uv pip install pyyaml  # 如需手动安装
  ```
- 新增依赖请同步更新 `pyproject.toml` 并在 PR 说明中注明

## 交流与支持
- 通过 [GitHub Discussions](https://github.com/alpha-keystone/fastapi-keystone/discussions) 参与社区讨论
- 安全问题请参考 [SECURITY.md](./SECURITY.md)
- 也可通过 issue 或邮箱与 Maintainer 联系

## 贡献者公约
- 尊重他人，友善交流
- 遵守开源协议（MIT License）
- 共同维护高质量、可持续的开源社区

---

再次感谢你的贡献！让我们一起让 fastapi-keystone 更好！ 