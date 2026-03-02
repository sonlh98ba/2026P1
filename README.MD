🏦 Mini Banking System

Ledger Model + Audit Logging + Elasticsearch + Kibana

1. Giới thiệu

Dự án này mô phỏng kiến trúc Core Banking thực tế của ngân hàng, bao gồm:

Backend: FastAPI + SQLAlchemy + Ledger model

Frontend: Vue 3 + TailwindCSS

Audit Logging: Elasticsearch + Kibana

Logging kiến trúc enterprise:

Business error logging

Validation error logging

System error logging (500 + stack trace)

2. Kiến trúc tổng thể
Vue Frontend
     ↓
FastAPI Backend
     ↓
Ledger Model + PostgreSQL
     ↓
Audit Logging Middleware
     ↓
Elasticsearch
     ↓
Kibana (SIEM Dashboard)

3. Yêu cầu hệ thống

Máy mới chưa cài gì cần chuẩn bị:

Windows 10/11 / macOS / Linux

Quyền cài đặt phần mềm

Kết nối Internet

4. Cài đặt môi trường từ máy trống
4.1. Cài Git
Windows

Tải tại:

https://git-scm.com/download/win


Cài mặc định → Next → Finish.

Kiểm tra:

git --version

macOS
brew install git

Linux (Ubuntu)
sudo apt update
sudo apt install git -y

4.2. Cài Python
Windows

Tải tại:

https://www.python.org/downloads/


Quan trọng: tick chọn

☑ Add python.exe to PATH


Kiểm tra:

python --version
pip --version

macOS
brew install python

Linux
sudo apt install python3 python3-pip python3-venv -y

4.3. Cài Node.js

Tải tại:

https://nodejs.org/en/download


Chọn bản LTS.

Kiểm tra:

node -v
npm -v

4.4. Cài Docker Desktop
Windows / macOS

Tải tại:

https://www.docker.com/products/docker-desktop


Cài mặc định.

Kiểm tra:

docker -v
docker compose version

5. Clone source code
git clone <REPO_URL>
cd 2026P1

6. Setup Elasticsearch + Kibana (Audit Logging)
6.1. Tạo file docker-compose.yml

Tại thư mục gốc project:

2026P1/docker-compose.yml


Nội dung:

version: "3.8"

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.12.0
    container_name: elasticsearch
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - ES_JAVA_OPTS=-Xms512m -Xmx512m
    ports:
      - "9200:9200"
    volumes:
      - esdata:/usr/share/elasticsearch/data

  kibana:
    image: docker.elastic.co/kibana/kibana:8.12.0
    container_name: kibana
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch

volumes:
  esdata:

6.2. Khởi động ELK stack
docker compose up -d


Kiểm tra:

Elasticsearch: http://localhost:9200

Kibana: http://localhost:5601

7. Setup Backend (FastAPI + Ledger + Audit logging)
7.1. Tạo virtual environment
cd backend
python -m venv venv


Kích hoạt:

Windows

venv\Scripts\activate


macOS / Linux

source venv/bin/activate

7.2. Cài dependencies
pip install fastapi uvicorn sqlalchemy psycopg2-binary elasticsearch==8.12.0 python-dotenv

7.3. Chạy backend
uvicorn app.main:app --reload


Backend chạy tại:

http://localhost:8000


Swagger UI:

http://localhost:8000/docs

8. Setup Frontend (Vue 3)
8.1. Cài node modules
cd frontend/vue-app
npm install

8.2. Chạy frontend
npm run dev


Frontend chạy tại:

http://localhost:5173

9. Setup Kibana Audit Logging Dashboard
9.1. Tạo Data View

Truy cập:

http://localhost:5601


Vào:

☰ → Stack Management → Data Views → Create data view


Nhập:

Name: banking-audit-v3
Index pattern: banking-audit-v3*
Time field: @timestamp

9.2. Truy cập log
☰ → Analytics → Discover → banking-audit-v3*

10. Kiến trúc Logging & Error Handling
10.1. Các loại log
Loại	Mô tả
BUSINESS_ERROR	Lỗi nghiệp vụ (4xx)
VALIDATION_ERROR	Lỗi validate request (422)
SYSTEM_ERROR	Lỗi hệ thống (500 + stacktrace)
10.2. Pipeline xử lý lỗi
Request
   ↓
Validation Handler (422)
   ↓
HTTPException Handler (4xx)
   ↓
Global Exception Handler (500)
   ↓
Audit Logger
   ↓
Elasticsearch
   ↓
Kibana SIEM Dashboard

11. Kiến trúc hệ thống tổng thể
Vue UI
   ↓
FastAPI Backend
   ↓
Ledger Accounting Model
   ↓
Audit Logging Layer
   ↓
Elasticsearch
   ↓
Kibana SIEM

12. Ghi chú vận hành

Docker phải luôn chạy trước backend.

Elasticsearch phải sẵn sàng trước khi backend khởi động.

Nếu đổi schema log → tạo index version mới (banking-audit-v4, v5...).

13. Định hướng mở rộng

Kafka streaming

Fraud Detection Engine

Realtime Alert (Slack / Email)

Executive Dashboard

Risk scoring engine

14. Mức độ hoàn thiện hệ thống

Hệ thống hiện tại đạt chuẩn:

Enterprise Core Banking Demo + SIEM Observability Platform