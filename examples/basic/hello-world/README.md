# Hello World 示例

这是最简单的 FastAPI Keystone 应用示例，展示框架的基本用法。

## 功能特性

- 基础路由定义
- 标准化API响应
- 最小配置启动

## 文件说明

- `main.py` - 应用主入口
- `requirements.txt` - 项目依赖

## 运行方式

```bash
# 安装依赖
uv pip install -r requirements.txt

# 运行应用
python main.py
```

## API 端点

- `GET /` - 返回欢迎消息
- `GET /hello/{name}` - 个性化问候
- `GET /health` - 健康检查

## 访问地址

应用启动后，访问：
- http://localhost:8000 - 主页
- http://localhost:8000/docs - API文档
- http://localhost:8000/hello/world - 示例API

## 学习要点

1. 如何创建 FastAPI Keystone 应用
2. 基础路由定义方法
3. 使用 APIResponse 返回标准化响应
4. 启动和配置服务器 