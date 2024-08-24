# Llama2API

Llama2API 是一个基于 FastAPI 构建的 API 服务，用于处理特定任务。该服务通过 Docker 容器化，以便于部署和管理。

## 目录结构

```text
llama2api/
├── llama2api.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## 先决条件

在开始之前，请确保你已经安装了以下软件：

- [Docker](https://www.docker.com/get-started)

## 构建 Docker 镜像

首先，克隆这个仓库并进入项目目录：

```sh
git clone https://github.com/yourusername/llama2api.git
cd llama2api
```

然后，构建 Docker 镜像：

```sh
docker build -t llama2api .
```

## 运行 Docker 容器

使用以下命令运行 Docker 容器：

```sh
docker run -p 9999:9999 llama2api
```

这将启动一个容器并在本地的 9999 端口上运行该应用程序。

## 使用 API

启动容器后，你可以通过以下 URL 访问 API：

```text
http://localhost:9999
```

你可以使用工具如 `curl` 或 Postman 来测试 API 端点。例如，要获取模型列表，可以发送 GET 请求到：

```text
http://localhost:9999/v1/models
```

## 环境变量

这个项目使用 `.env` 文件来加载环境变量。在运行容器之前，请确保你已经在项目根目录下创建了一个 `.env` 文件，并添加了必要的环境变量，例如 `API_KEY`。

## 示例 .env 文件

```text
API_KEY=your_api_key_here
```

## 代码来源

```text
https://linux.do/t/topic/184940
```

## 许可证

这个项目使用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
