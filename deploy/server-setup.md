# AIFriends 云服务器部署

以下命令假设项目目录为 `/home/acs/AIFriends`，登录用户为 `acs`。

## 1. 上传项目

在本机 Git Bash（不是服务器 SSH 会话）执行：

```bash
scp -r /d/AIFriends acs@服务器公网IP:/home/acs/
```

不要上传本机 `.venv` 和 `frontend/node_modules`；若使用 Git，同步代码后直接在服务器 `git pull` 即可。

## 2. 安装与初始化

在服务器执行：

```bash
cd ~/AIFriends
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ../backend
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py check --deploy
```

## 3. 后端环境变量

编辑 `/home/acs/AIFriends/backend/.env`，至少包含：

```dotenv
API_KEY=你的百炼API_KEY
API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
DJANGO_DEBUG=false
DJANGO_SECRET_KEY=请替换为随机长字符串
```

随机密钥可在服务器生成：

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## 4. 配置 systemd 与 Nginx

```bash
sudo cp ~/AIFriends/deploy/aifriends.service /etc/systemd/system/aifriends.service
sudo systemctl daemon-reload
sudo systemctl enable --now aifriends
sudo cp ~/AIFriends/deploy/nginx-aifriends.conf /etc/nginx/sites-available/aifriends
sudo ln -sfn /etc/nginx/sites-available/aifriends /etc/nginx/sites-enabled/aifriends
sudo nginx -t
sudo systemctl reload nginx
```

检查状态：

```bash
sudo systemctl status aifriends --no-pager
sudo journalctl -u aifriends -n 100 --no-pager
curl -I http://127.0.0.1:8000
curl -I http://127.0.0.1 -H 'Host: app8137.acapp.acwing.com.cn'
```

HTTPS 证书由域名平台提供时，保持平台的代理配置；若服务器自行管理证书，再使用 Certbot 配置 443。
