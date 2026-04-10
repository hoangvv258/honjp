# HonJP - Ứng dụng học tiếng Nhật

Ứng dụng web học tiếng Nhật với giao diện hiện đại, hỗ trợ từ vựng, Kanji, ngữ pháp từ N5 đến N1.

## Tính năng

- 📖 **Từ vựng**: 6,289 từ với cách đọc, nghĩa, ví dụ, kanji liên quan
- 🈶 **Kanji**: 2,215 chữ Hán với bộ thủ, âm on/kun, từ vựng liên quan
- 📝 **Ngữ pháp**: 3,206 mẫu câu với cấu trúc, giải thích, ví dụ
- 🃏 **Flashcard**: Ôn tập bằng thẻ ghi nhớ
- 🧠 **Quiz**: Kiểm tra trắc nghiệm
- 🔖 **Đánh dấu**: Đánh dấu "Cần ôn lại" / "Đã học" với bộ lọc
- 🌙 **Dark/Light mode**: Giao diện glassmorphism 2026

## Cài đặt

```bash
# Clone repo
git clone https://github.com/hoangvv258/honjp.git
cd honjp

# Tạo virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Cài đặt dependencies
pip install -r requirements.txt

# Tạo database
python init_db.py

# Chạy ứng dụng
python app.py
```

Truy cập: http://localhost:5000

## Tech Stack

- **Backend**: Python 3 + Flask + SQLite
- **Frontend**: Vanilla JS + Jinja2 templates
- **UI**: Glassmorphism, CSS custom properties, Google Fonts (Inter + Noto Sans JP)
