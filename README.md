# Diplom Monitoring

Bu loyiha Docker asosida Droplet serverga moslangan.

## Ishga tushirish tartibi

1. Repo'ni serverga yuklang:
   ```bash
   git clone <your-repo-url>
   cd diplom_monitoring
   ```

2. `.env.example` dan `.env` yarating va to'ldiring:
   - `DOMAIN=yourdomain.com`
   - `DATABASE_URL=postgresql+asyncpg://...`
   - `SECRET_KEY=...`
   - `POSTGRES_PASSWORD=...`

3. Domen DNS'ini Droplet IP'iga yo'naltiring.

4. Prod stack'ni ishga tushiring:
   ```bash
   docker compose -f docker-compose.prod.yml up -d --build
   ```

5. Tekshiring:
   ```bash
   docker compose -f docker-compose.prod.yml ps
   docker compose -f docker-compose.prod.yml logs -f nginx
   docker compose -f docker-compose.prod.yml logs -f backend
   ```

## Muhim eslatmalar

- `deploy/nginx.conf` endi nginx template sifatida ishlaydi va `DOMAIN` orqali to'ldiriladi.
- Frontend chat uchun WebSocket ishlaydi, lekin polling fallback ham saqlangan.
- `passenger_wsgi.py` va `CPANEL_DEPLOY.md` cPanel uchun eski fayllar edi; Droplet uchun kerak emas.

## Lokal frontend build

Agar frontend'ni alohida tekshirmoqchi bo'lsangiz:

```bash
cd frontend
npm install
npm run build
```

