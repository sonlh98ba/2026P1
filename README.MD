# 2026P1 - AIOps Platform Setup Guide (New Machine)

Huong dan nay giup ban cai va chay project tren may moi mot cach on dinh.

## 1. Yeu cau he thong

- Git
- Python 3.11 hoac 3.12
- Node.js 20 LTS (khuyen nghi)
- PostgreSQL 14+
- Docker Desktop (de chay Elasticsearch + Kibana)

Kiem tra nhanh:

```powershell
git --version
python --version
node -v
npm -v
docker -v
docker compose version
psql --version
```

## 2. Clone source

```powershell
git clone https://github.com/sonlh98ba/2026P1.git
cd 2026P1
```

## 3. Khoi dong Elasticsearch + Kibana

Project su dung file compose tai `aiops-platform/docker-compose.yml`.

```powershell
cd aiops-platform
docker compose up -d
```

Kiem tra:

- Elasticsearch: `http://localhost:9200`
- Kibana: `http://localhost:5601`

## 4. Tao database PostgreSQL

Backend dang mac dinh ket noi:

`postgresql://postgres:postgres@localhost:5432/aiops`

Tao DB:

```powershell
createdb -U postgres aiops
```

Neu may chua co role `postgres`/mat khau khac, hay tao role hoac sua lai chuoi ket noi trong `aiops-platform/backend/app/database.py`.

## 5. Import schema vao DB

Da co san file schema:

`aiops-platform/backend/schema.sql`

Import:

```powershell
psql -U postgres -d aiops -f .\aiops-platform\backend\schema.sql
```

## 6. Cai va chay Backend (FastAPI)

```powershell
cd aiops-platform\backend
python -m venv venv
.\venv\Scripts\activate
pip install --upgrade pip
pip install fastapi uvicorn sqlalchemy psycopg2-binary elasticsearch==8.12.0 python-dotenv
uvicorn app.main:app --reload
```

Backend:

- API root: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## 7. Cai va chay Frontend (Vue 3 + Vite)

Mo terminal moi:

```powershell
cd 2026P1\aiops-platform\frontend\aiops-dashboard
npm install
npm run dev
```

Frontend:

- `http://localhost:5173`

## 8. Kiem tra nhanh sau khi chay

1. `http://localhost:9200` tra ve JSON.
2. `http://localhost:8000/health` tra ve `{"status":"ok"}`.
3. `http://localhost:5173` mo duoc dashboard.
4. `http://localhost:8000/docs` load duoc schema API.

## 9. Xuat lai schema khi model thay doi

Neu ban sua model SQLAlchemy, xuat lai schema bang:

```powershell
$env:PYTHONPATH="c:\path\to\2026P1\aiops-platform\backend"
.\aiops-platform\backend\venv\Scripts\python.exe .\aiops-platform\backend\scripts\export_schema.py
```

File ket qua: `aiops-platform/backend/schema.sql`

## 10. Su co thuong gap

- `connection refused localhost:9200`:
  - Elasticsearch chua chay. Chay lai `docker compose up -d` trong `aiops-platform`.
- `password authentication failed for user postgres`:
  - Sai mat khau DB. Sua `DATABASE_URL` trong `backend/app/database.py`.
- Frontend khong goi duoc backend:
  - Dam bao backend dang chay cong `8000` va frontend la `5173`.

## 11. Ghi chu bo sung

- Thu muc `venv`, `node_modules`, `__pycache__` da duoc ignore boi `.gitignore`.
- Neu can setup project `banking-system` (module cu), hay tao huong dan rieng; README nay uu tien luong chay cho `aiops-platform`.
