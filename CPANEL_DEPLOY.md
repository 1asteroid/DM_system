# cPanel Python App uchun deploy yo'riqnomasi

Bu loyiha cPanel Python App’da quyidagicha ishga tushiriladi:

## 1) cPanel maydonlarini to'ldirish

Agar loyiha papkangiz mana bunday bo'lsa:

- `/home/USERNAME/diplom_monitoring/`
  - `backend/`
  - `frontend/`

unda cPanel’da quyidagilarni yozing:

- **Ilova ildiz katalogi**: `/home/USERNAME/diplom_monitoring/backend`
- **Ilova URL manzili**: `domeningiz.uz`
- **Ilovani ishga tushirish fayli**: `passenger_wsgi.py`
- **Ilovaga kirish nuqtasi**: `application`
- **Yo'lovchi jurnali fayli**: `/home/USERNAME/logs/diplom_monitoring_passenger.log`

## 2) Kerakli fayllar

- `backend/passenger_wsgi.py` — cPanel uchun WSGI bridge
- `backend/app/main.py` — backend API + frontend build’ni bir domen ostida ko'rsatish
- `.env` — maxfiy sozlamalar

## 3) cPanel’da DB sozlash

Agar VPS/PostgreSQL bo'lmasa, `.env` ichida SQLite ishlating:

```env
DATABASE_URL=sqlite+aiosqlite:///./data/diplom.db
```

Agar alohida PostgreSQL bo'lsa:

```env
DATABASE_URL=postgresql+asyncpg://postgres:PAROL@HOST:5432/diplom_db
```

## 4) Frontend build

Loyihaning frontend qismini lokal kompyuteringizda build qiling:

```bash
cd frontend
npm install
npm run build
```

So'ng `frontend/dist` papkasini serverga yuklang.

## 5) Ishga tushirish tartibi

1. Repo’ni serverga joylang.
2. `.env.example` dan `.env` yarating.
3. `frontend/dist` yuklanganini tekshiring.
4. cPanel Python App’ni yaratib, yuqoridagi maydonlarni to'ldiring.
5. App’ni qayta ishga tushiring.

## 6) Eslatma

Bu hostingda WebSocket ishlamasligi mumkin. Shuning uchun `Messages` sahifasiga polling fallback qo'shilgan. Bu xabarlar yangilanishini refresh qilmasdan ham ko'rsatishga yordam beradi.

