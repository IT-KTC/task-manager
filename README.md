# Task Manager — Django Web App & REST API

> **Repository:** [IT-KTC/task-manager](https://github.com/IT-KTC/task-manager)  
> **Nhánh dùng làm cơ sở:** [`develop`](https://github.com/IT-KTC/task-manager/tree/develop)

## 1. Giới thiệu

Task Manager là ứng dụng quản lý công việc viết bằng **Django**. Người dùng có thể đăng ký, đăng nhập, quản lý Task cá nhân, tìm kiếm, lọc, sắp xếp, theo dõi tiến độ và sử dụng Kanban Board. Dự án còn có REST API qua Django REST Framework và phần xử lý ảnh bất đồng bộ với Celery/Redis.

Các mục tiêu chính:

- CRUD Task và bảo vệ dữ liệu theo người sở hữu (`Task.user` / `request.user`).
- Dashboard thống kê và danh sách Task của **người đang đăng nhập**.
- Trạng thái (`pending`, `in_progress`, `completed`), ưu tiên và hạn hoàn thành.
- Upload tệp/ảnh, API và kiểm thử.
- Django Admin mặc định để quản lý dữ liệu.

**Phân biệt:** Dashboard `/tasks/dashboard/` là dashboard **cá nhân**, không phải dashboard toàn hệ thống. Gói `admin_panel` đã chuẩn bị riêng trước đó **chưa nằm trong nhánh `develop`**; nếu tích hợp mới có `/management/`.

## 2. Công nghệ & kiến trúc

| Thành phần           | Công nghệ đã kiểm tra trong source                                     |
| -------------------- | ---------------------------------------------------------------------- |
| Ngôn ngữ ứng dụng    | Python; Dockerfile dùng image `python:3.14-slim`                       |
| Backend              | Django `6.1.1` (requirements.txt)                                      |
| API                  | Django REST Framework `3.18.3`, Simple JWT `5.5.1`                     |
| DB trên Docker/local | PostgreSQL (`postgres:18` trong Compose)                               |
| Cache/broker         | Redis (`redis:7-alpine`), Celery `5.6.3`                               |
| Frontend             | Django Templates + HTML/CSS/JavaScript, **không phải Vue/React**       |
| File/ảnh             | Django FileField/ImageField + Pillow                                   |
| PythonAnywhere       | Cấu hình riêng trong `task_manager/settings.py`: SQLite + locmem cache |
| Kiểm thử             | Django test runner, `tasks/tests.py`, `accounts/tests.py`              |

Kiến trúc ứng dụng là **Django web app** với các Django App `tasks`, `accounts`; Django Admin là thành phần built-in. API và các view Template cùng nằm trong một backend.

## 3. Cấu trúc thư mục

```text
Task Manager/
├── accounts/
│   ├── views.py                 # register / login / logout
│   ├── security.py              # giới hạn request đăng nhập
│   ├── urls.py
│   └── tests.py
├── tasks/
│   ├── models.py                # Task, TaskQuerySet
│   ├── views.py                 # CRUD, Dashboard, Kanban
│   ├── forms.py                 # kiểm tra dữ liệu Task và file upload
│   ├── services.py              # logic thay đổi trạng thái
│   ├── serializers.py           # DRF TaskSerializer
│   ├── api_views.py             # TaskViewSet
│   ├── permissions.py           # IsOwner
│   ├── tasks.py                 # Celery task
│   ├── admin.py                 # đăng ký Task vào Django Admin
│   ├── management/commands/
│   │   ├── task_report.py       # CÓ SẴN trên GitHub
│   │   └── seed_demo.py         # MỚI — từ gói bổ sung này
│   └── tests_seed_demo.py       # MỚI — test cho lệnh seed
├── task_manager/
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── templates/base.html
├── static/
├── media/
├── compose.yaml
├── Dockerfile
├── requirements.txt
├── .env.example                 # MỚI — file mẫu từ gói bổ sung
└── README.md                    # MỚI — tài liệu này
```

## 4. Các chức năng đã có trên nhánh `develop`

| Nhóm           | Chức năng                                               |
| -------------- | ------------------------------------------------------- |
| Authentication | Đăng ký, đăng nhập bằng session, đăng xuất qua POST     |
| Tasks          | Tạo, đọc, sửa, xóa, xem chi tiết Task theo User         |
| Trạng thái     | `pending`, `in_progress`, `completed`, quick-status     |
| Priority       | `low`, `medium`, `high`                                 |
| Deadline       | `due_date`, `is_overdue`                                |
| Dashboard      | Tổng hợp Task của User hiện tại; Task mới nhất          |
| Kanban         | Cột trạng thái, di chuyển Task (request POST)           |
| Search/Filter  | Title, status, priority, quá hạn, sắp xếp, phân trang   |
| Upload         | Tệp đính kèm, ảnh và tải lại theo kiểm tra quyền sở hữu |
| REST API       | TaskViewSet, GET/POST/PATCH/DELETE, search/order, stats |
| Auth API       | JWT access/refresh token                                |
| Worker         | Celery task xử lý ảnh qua Redis broker                  |
| Admin          | `/admin/` Django built-in, có đăng ký Task model        |

> Các chức năng trên đã được xác nhận **có mã nguồn**. Đây không phải tuyên bố rằng tất cả chức năng đã được kiểm thử thành công trong môi trường hiện tại.

## 5. Cài đặt đề xuất: Docker Compose (Windows PowerShell)

### 5.1. Yêu cầu

- Git.
- Docker Desktop có Docker Compose.
- Port `8000` chưa bị ứng dụng khác chiếm.

### 5.2. Clone đúng repository và đúng nhánh

```powershell
git clone -b develop https://github.com/IT-KTC/task-manager.git
cd task-manager
```

> Nếu đã clone sẵn, kiểm tra `git remote -v` và `git branch --show-current` trước khi thao tác. Không chạy `git reset --hard` để chuyển nhánh nếu đang có thay đổi chưa commit.

### 5.3. Chép ba tệp seed và file env mẫu vào repository

Từ ZIP bổ sung kèm theo tài liệu, sao chép vào repo:

```text
README.md
.env.example
tasks/management/commands/seed_demo.py
tasks/tests_seed_demo.py
```

Giữ lại `tasks/management/commands/__init__.py` vốn đã tồn tại trên nhánh `develop`.

### 5.4. Tạo `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

**Bạn phải sửa các placeholder** trong `.env` trước khi chạy Docker:

- `SECRET_KEY`: chuỗi ngẫu nhiên đủ dài, chỉ dùng cho local.
- `DB_PASSWORD`: mật khẩu PostgreSQL local.
- `TASK_MANAGER_DEMO_PASSWORD`: một mật khẩu test mạnh, **tối thiểu 12 ký tự**, chỉ dùng trong môi trường thử nghiệm.
- Giữ `DJANGO_ENV=local`, `DEBUG=true`, `DB_HOST=db` khi chạy Docker theo Compose của repo.

Ví dụ các tên biến (không điền nguyên các placeholder):

```dotenv
DJANGO_ENV=local
DEBUG=true
SECRET_KEY=<chuoi-bi-mat-rieng-cua-ban>
ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=task_manager_local
DB_USER=task_manager_local
DB_PASSWORD=<mat-khau-postgresql-rieng>
DB_HOST=db
DB_PORT=5432
CELERY_BROKER_URL=redis://redis:6379/0
TASK_MANAGER_DEMO_PASSWORD=<mat-khau-demo-tu-dat-toi-thieu-12-ky-tu>
```

Không đưa `.env` vào Git. Repository đã có quy tắc ignore `.env`.

### 5.5. Khởi chạy & migrate

```powershell
docker compose up -d --build
docker compose ps
docker compose exec web python manage.py migrate
docker compose exec web python manage.py check
```

Ứng dụng: <http://localhost:8000/>. Xem log khi cần:

```powershell
docker compose logs -f web
docker compose logs -f celery
```

Nếu không có Docker, có thể dùng virtual environment với `pip install -r requirements.txt`; tuy nhiên nhánh `develop` mặc định cấu hình **PostgreSQL** ngoài PythonAnywhere, và Compose **không publish port 5432**. Vì vậy cần chuẩn bị PostgreSQL/Redis và biến môi trường thích hợp; không thể tự giả định SQLite cho local.

## 6. Tài khoản thử nghiệm: được tạo bằng `seed_demo`

**Các tài khoản dưới đây là bộ fixture mới do tài liệu này cung cấp, không phải tài khoản có sẵn trong source gốc hoặc DB của bạn.**

| Username        | Loại tài khoản | Active    | Quyền / mục đích test                                                  | Task mẫu |
| --------------- | -------------- | --------- | ---------------------------------------------------------------------- | -------: |
| `demo_admin`    | Superuser      | Có        | Vào `/admin/`; vào `/management/` nếu đã tích hợp `admin_panel`        |        0 |
| `demo_staff`    | Staff          | Có        | Django Admin **chỉ xem** User và Task thông qua Group `DEMO_READ_ONLY` |        0 |
| `demo_alice`    | User thường    | Có        | Test CRUD, lọc, priority, overdue, upload                              |        4 |
| `demo_bob`      | User thường    | Có        | Test quyền sở hữu, dữ liệu của User thứ hai                            |        4 |
| `demo_empty`    | User thường    | Có        | Test dashboard/list rỗng, không chia 0                                 |        0 |
| `demo_inactive` | User thường    | **Không** | Test tài khoản bị khóa không thể đăng nhập                             |        0 |

**Mật khẩu:** Tất cả tài khoản test được tạo mới dùng giá trị từ `TASK_MANAGER_DEMO_PASSWORD` trong `.env`. Không có mật khẩu hardcode trong Python hoặc README. Không hiển thị mật khẩu ra log.

Các email có dạng `@example.invalid` — là dữ liệu giả để thử nghiệm, không dùng gửi email thật.

### 6.1. Chạy seed đầy đủ

Sau khi migrate thành công:

```powershell
docker compose exec web python manage.py seed_demo
```

Kết quả lần đầu, nếu chưa có tài khoản và Task mẫu:

```text
Seed completed: 6 new users, 8 new Tasks.
Accounts: demo_admin, demo_staff, demo_alice, demo_bob, demo_empty, demo_inactive
Password: from TASK_MANAGER_DEMO_PASSWORD (not printed).
```

Kiểm tra tổng Task trên DB:

```powershell
docker compose exec web python manage.py task_report
```

Lưu ý: `task_report` báo tổng Task **của toàn database**, không chỉ Task demo. Nếu DB đã có dữ liệu, kết quả có thể lớn hơn 8.

### 6.2. Seed có tạo trùng không?

Không. Lệnh sử dụng `get_or_create()` cho Task theo `(user, title)`; User cũng được nhận diện theo `username`.

Chạy lại:

```powershell
docker compose exec web python manage.py seed_demo
```

Lệnh không tạo thêm 6 User và 8 Task nếu dữ liệu demo đã tồn tại; không xóa dữ liệu, không ghi đè Task và không đổi role/active/password của User có sẵn.

### 6.3. Reset mật khẩu test khi quên

Sửa `TASK_MANAGER_DEMO_PASSWORD` trong `.env` (rồi **khởi tạo lại container** để đọc env mới nếu cần):

```powershell
docker compose up -d --force-recreate web
docker compose exec web python manage.py seed_demo --reset-password
```

`--reset-password` **chỉ đổi mật khẩu** cho các username demo đã tồn tại; không cấp thêm quyền Superuser cho tài khoản cũ. Nếu Username đã tồn tại trước seed với phân quyền khác, kiểm tra thủ công thay vì mong lệnh tự thay đổi quyền.

### 6.4. Bảo mật khi seed

- Chỉ chạy trên database thử nghiệm riêng với `DJANGO_ENV=local`, `development` hoặc `test`.
- Lệnh từ chối chạy nếu `DJANGO_ENV=pythonanywhere` hoặc giá trị môi trường ngoài danh sách local/test.
- **Không chạy seed trong production hoặc trên dữ liệu thật**; quyền Superuser mặc định từ seed chỉ dành cho demo.
- Đổi mật khẩu test trong `.env` theo dự án; không chia sẻ `.env`.
- Không đưa mã băm hay mật khẩu của người dùng thật vào seed hoặc README.

## 7. Bộ Task mẫu được tạo

Các `due_date` dưới đây tính **tương đối so với ngày chạy seed lần đầu**.

| User       | Task                       | Status      | Priority | Due date                         |
| ---------- | -------------------------- | ----------- | -------- | -------------------------------- |
| demo_alice | Tìm hiểu Django ORM        | pending     | high     | 2 ngày trước → quá hạn           |
| demo_alice | Viết API Task              | in_progress | high     | Sau 2 ngày                       |
| demo_alice | Hoàn thiện trang đăng nhập | completed   | medium   | 1 ngày trước, không tính quá hạn |
| demo_alice | Lập kế hoạch Sprint        | pending     | low      | Không có deadline                |
| demo_bob   | Kiểm tra user ownership    | completed   | high     | Hôm nay                          |
| demo_bob   | Thiết kế Kanban            | in_progress | medium   | Sau 7 ngày                       |
| demo_bob   | Viết unit test             | pending     | medium   | Sau 1 ngày                       |
| demo_bob   | Kiểm tra task quá hạn      | pending     | low      | 3 ngày trước → quá hạn           |

Các Task được đánh dấu `[DEMO]` trong tiêu đề và không chứa file/ảnh thật. Nếu Task đã tồn tại, chạy seed lại **không cập nhật deadline theo ngày mới**; đây là lựa chọn để tránh ghi đè dữ liệu thử nghiệm đã chỉnh sửa.

## 8. Đường dẫn Web và API

### Giao diện

| Trang                  | Đường dẫn             | Ghi chú                                                               |
| ---------------------- | --------------------- | --------------------------------------------------------------------- |
| Trang chủ              | `/`                   | Redirect đến dashboard cá nhân                                        |
| Đăng nhập              | `/accounts/login/`    | User active                                                           |
| Đăng ký                | `/accounts/register/` | Tạo User thường                                                       |
| Công việc của tôi      | `/tasks/`             | Chỉ Task của người đăng nhập                                          |
| Tạo Task               | `/tasks/create/`      | Login required                                                        |
| Dashboard cá nhân      | `/tasks/dashboard/`   | Thống kê theo `request.user`                                          |
| Kanban                 | `/tasks/kanban/`      | Kéo thả/đổi trạng thái Task                                           |
| Django Admin           | `/admin/`             | Có sẵn trên `develop`                                                 |
| Custom Admin Dashboard | `/management/`        | **Chỉ có nếu cài gói `admin_panel` bổ sung; chưa có trong `develop`** |

### REST API

| Method | Endpoint              | Công dụng                         |
| ------ | --------------------- | --------------------------------- |
| GET    | `/api/tasks/`         | List Task của User được xác thực  |
| POST   | `/api/tasks/`         | Tạo Task và tự gắn `request.user` |
| GET    | `/api/tasks/{id}/`    | Chi tiết Task của chính User      |
| PATCH  | `/api/tasks/{id}/`    | Cập nhật Task của chính User      |
| DELETE | `/api/tasks/{id}/`    | Xóa Task của chính User           |
| GET    | `/api/tasks/stats/`   | Thống kê Task theo User           |
| POST   | `/api/token/`         | Cấp cặp JWT access/refresh        |
| POST   | `/api/token/refresh/` | Làm mới access token              |

API không có quyền `admin all users` được triển khai riêng trong nhánh `develop`. Các API Task dùng `IsAuthenticated` và `IsOwner`, query giới hạn theo User.

## 9. Quyền truy cập và các trường User

Dự án dùng Django built-in User (file `accounts/models.py` chưa định nghĩa custom user). Các trường có thể xem qua Django Admin và `admin_panel` (nếu cài):

`id`, `username`, `first_name`, `last_name`, `email`, `is_active`, `is_staff`, `is_superuser`, `groups`, `user_permissions`, `date_joined`, `last_login`.

Không có field trong DB hiện tại cho `phone`, `address`, `avatar`, `department`. Không được tự hiểu những thông tin đó đã có sẵn. Không hiển thị mật khẩu hoặc password hash trên dashboard riêng.

**Lưu ý:** `last_login` là thời điểm đăng nhập gần nhất, **không phải trạng thái online**.

## 10. Hướng dẫn kiểm thử nhanh

1. Đăng nhập `demo_admin`, mở `/admin/`; nếu đã cài `admin_panel`, mở `/management/` và xem số User/Task.
2. Đăng nhập `demo_alice`, mở Dashboard và Kanban. Kiểm tra chỉ thấy 4 Task của Alice, gồm Task đang chờ, đang thực hiện, hoàn thành và quá hạn.
3. Đăng nhập `demo_bob`. Thử mở/sửa/xóa Task của Alice qua URL/API; phải không xem/sửa được Task của Alice.
4. Đăng nhập `demo_empty`; Dashboard phải xử lý danh sách rỗng mà không lỗi.
5. Đăng nhập `demo_inactive`; phải bị từ chối do tài khoản không hoạt động.
6. Đăng nhập `demo_staff`; xem User/Task trong Django Admin bằng quyền **view**, không có quyền thêm/sửa/xóa.
7. Dùng `demo_alice` tạo Task mới và upload tệp hợp lệ, xác minh form validation và quyền tải.

Chạy test tự động:

```powershell
docker compose exec web python manage.py test tasks.tests_seed_demo -v 2
docker compose exec web python manage.py test tasks accounts -v 2
```

**Lưu ý về chất lượng nhánh `develop`**: trong `tasks/admin.py` đang có typo `search_fields = ("title", "discription")`, trong khi model là `description`. Trước khi test tìm kiếm trong Django Admin, sửa `discription` thành `description` (nếu chưa sửa).

## 11. Xem lỗi và khắc phục thường gặp

| Hiện tượng                   | Kiểm tra                                                                 |
| ---------------------------- | ------------------------------------------------------------------------ |
| Không vào được trang         | `docker compose ps`, `docker compose logs web`                           |
| Chưa có bảng DB              | `docker compose exec web python manage.py migrate`                       |
| Không đăng nhập được demo    | Đã chạy `seed_demo`? Password trong `.env` có đúng? Tài khoản có Active? |
| Admin không hiện Task        | Cần kiểm tra `tasks/admin.py`, quyền của User, migration                 |
| Staff không sửa được Task    | **Đúng thiết kế:** `demo_staff` chỉ có view permissions                  |
| Trang `/management/` báo 404 | Chưa tích hợp `admin_panel` bổ sung                                      |
| Celery không chạy            | `docker compose logs celery`; Redis và broker URL                        |
| File/ảnh không hiển thị      | Kiểm tra `MEDIA_ROOT`, DEBUG, quyền Task, storage                        |
| DB local khác DB Docker      | Kiểm tra `DB_HOST`, `DJANGO_ENV`, container và `.env`                    |

### Những điều chưa được xác minh

- Chưa chạy Django test thực tế trên database/container của bạn bằng phiên bản README + seed mới.
- Chưa xác nhận Admin Dashboard tùy chỉnh đã được chép vào repo hoặc triển khai; đó là gói bổ sung **riêng**, không phải tính năng có sẵn trên nhánh `develop`.
- Chưa có bằng chứng môi trường production chạy ổn định; cấu hình môi trường khác nhau đáng kể giữa Docker/PostgreSQL và PythonAnywhere/SQLite.

## 12. Git workflow và đóng góp

```powershell
git status
git switch develop
git pull origin develop
git switch -c docs/readme-and-demo-seed
# Chép/cập nhật các file từ gói bổ sung
# Chạy migrate, seed, test và kiểm tra thay đổi
git add README.md .env.example tasks/management/commands/seed_demo.py tasks/tests_seed_demo.py
git commit -m "docs: add project README and demo seed command"
git push -u origin docs/readme-and-demo-seed
```

Tạo Pull Request vào `develop` sau khi đã kiểm thử. **Không commit `.env` hoặc password thật.**

---

