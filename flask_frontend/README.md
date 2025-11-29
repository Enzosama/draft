## Flask frontend (wrap React UI, không cần Vite/npm khi chạy)

Thư mục này chứa một Flask app rất mỏng để **serve UI React đã build sẵn**
mà **không thay đổi logic và cấu trúc code cũ**.

### Cấu trúc chính

- `app.py`: Flask app
  - `GET /`: trả về file `../frontend/dist/index.html`
  - `GET /assets/<file>`: serve bundle JS/CSS do Vite build ra (đã build sẵn)
- `requirements.txt`: khai báo dependency cho Flask

### Chạy ứng dụng mà KHÔNG cần Vite/npm

Chỉ cần Python + Flask:

```bash
cd /home/enzo/Documents/perl_python
source venv/bin/activate                    # trên Linux
pip install -r flask_frontend/requirements.txt
python -m flask --app flask_frontend.app run --host 0.0.0.0 --port 5000
```

Sau đó mở trình duyệt tại: `http://localhost:5000`.

- UI React chạy bằng bundle JS đã build sẵn trong `frontend/dist/assets`.
- **Không cần cài npm hay chạy Vite** để chạy production.

### Khi nào mới cần Vite/npm?

Chỉ khi bạn **sửa mã nguồn React** trong thư mục `frontend/` và muốn build lại bundle JS:

```bash
cd /home/enzo/Documents/perl_python/frontend
npm install        # chỉ cần lần đầu
npm run build      # build lại dist/ nếu có thay đổi React
```

Nếu bạn không còn thay đổi UI React nữa, bạn có thể bỏ qua hoàn toàn bước này
và chỉ cần dùng Flask để serve bundle đã build sẵn.



