# 🚀 AniGen: High-Concurrency AI Image Generation Backend

> 一个面向高并发场景设计的异步 AI 图像生成后端微服务。基于 FastAPI 与 Stable Diffusion 接口构建，采用 Redis 消息队列实现极致的 API 响应与任务解耦。

## ✨ 核心架构亮点 (Architecture Highlights)

- **全异步非阻塞 (Fully Async)**: 基于 `FastAPI` + `httpx` + `aiosqlite`，彻底榨干 IO 性能，拒绝线程阻塞。
- **分布式任务队列 (Distributed Task Queue)**: 引入 `ARQ` + `Redis`，将耗时的 AI 推理任务（如 SD/ComfyUI 调用）剥离出主进程，保障 Web 层的毫秒级响应，轻松应对流量洪峰。
- **高可用状态机 (Robust State Machine)**: 实现完整的任务生命周期追踪 (PENDING -> COMPLETED/FAILED)，配合底层网络超时截断（Timeout）与异常重试机制，防止算力节点宕机导致的数据混乱。
- **开箱即用 (Dockerized)**: 提供完整的 `docker-compose` 编排，一键拉起 API 网关、消息队列与后台消费节点。

## 🛠️ 技术栈 (Tech Stack)

- **Web Framework**: FastAPI, Pydantic (v2)
- **Message Queue**: Redis, ARQ (Async Redis Queue)
- **Database / ORM**: SQLite (Dev), SQLAlchemy 2.0 (Async)
- **AI Integration**: httpx (Stable Diffusion WebUI API)
- **DevOps**: Docker, Docker Compose

## 🚀 极速启动 (Quick Start)

本项目已完全容器化，环境零依赖。只需确保宿主机安装有 Docker 环境：

```bash
# 1. 克隆项目
git clone [https://github.com/YourUsername/anigen-backend-demo.git](https://github.com/YourUsername/anigen-backend-demo.git)
cd anigen-backend-demo

# 2. 一键启动微服务集群 (API + Redis + Worker)
docker-compose up -d --build

# 3. 访问 API 文档
# 打开浏览器访问: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
