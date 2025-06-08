# FastAPI Keystone Examples

这个目录包含了 FastAPI Keystone 框架的各种使用示例，从基础到高级应用场景。

## 📁 目录结构

```
examples/
├── basic/                  # 基础示例
│   ├── hello-world/       # 最简单的Hello World应用
│   ├── routing/           # 路由使用示例
│   └── config/            # 配置管理示例
├── intermediate/          # 中级示例
│   ├── dependency-injection/  # 依赖注入示例
│   ├── multi-tenant/      # 多租户应用示例
│   └── crud-api/          # CRUD API示例
├── advanced/              # 高级示例
│   ├── microservices/     # 微服务架构示例
│   ├── custom-middleware/ # 自定义中间件示例
│   └── testing/           # 测试示例
└── real-world/           # 真实项目示例
    ├── blog-api/         # 博客API
    ├── e-commerce/       # 电商系统
    └── saas-platform/    # SaaS平台示例
```

## 🚀 快速开始

每个示例目录都包含：
- `README.md` - 示例说明和使用方法
- `main.py` - 主程序入口
- `requirements.txt` - 依赖列表
- `config.json` - 配置文件（如果需要）

## 🔧 运行示例

1. 进入具体示例目录
2. 安装依赖：`uv pip install -r requirements.txt`
3. 运行示例：`python main.py`

## 📚 学习路径

建议按以下顺序学习：

1. **基础示例** - 了解框架基本概念
2. **中级示例** - 掌握核心特性
3. **高级示例** - 学习最佳实践
4. **真实项目** - 应用到实际开发

## 💡 贡献示例

欢迎提交新的示例！请确保：
- 代码简洁易懂
- 包含详细的README说明
- 添加必要的注释
- 遵循项目的代码规范 