FROM python:3.10-slim-bookworm
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
RUN pip install pip --upgrade

##工作目录
WORKDIR /app/starvlm

##copy source code
COPY . /app/starvlm/

##setup env
RUN pip install -r requirements.txt
ENTRYPOINT ["python", "app.py"]

