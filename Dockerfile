# 使用官方的 Python 镜像作为基础镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 将当前目录下的所有文件复制到工作目录
COPY . /app

# 安装 Python 依赖包
RUN pip install --no-cache-dir -r requirements.txt

# 暴露应用程序运行的端口
EXPOSE 9999

# 启动 FastAPI 应用
CMD ["uvicorn", "llama2api:app", "--host", "0.0.0.0", "--port", "9999"]