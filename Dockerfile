FROM python:3.10-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libc-dev libffi-dev libgmp-dev libmpfr-dev libmpc-dev

RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pip --upgrade

##工作目录
WORKDIR /app/starchat

##copy source code
COPY . /app/starchat/

##setup env
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "app.py"]

