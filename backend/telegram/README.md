# SafarSathi Telegram Bot

Local polling mode:

1. Put `TELEGRAM_BOT_TOKEN=...` in `backend/.env`.
2. From `backend/`, run:

   ```bash
   python -m telegram.polling
   ```

3. Open the bot in Telegram and send:
   - `/start`
   - `Parashar`
   - `Barot`
   - `Manali`
   - `Weather`
   - `Checklist`
   - `Emergency`
   - a location pin

Webhook mode:

1. Deploy the FastAPI app publicly over HTTPS.
2. Set `TELEGRAM_WEBHOOK_SECRET` in `backend/.env`.
3. Call:

   ```bash
   curl -X POST "https://YOUR_DOMAIN/telegram/webhook/set?url=https://YOUR_DOMAIN/telegram/webhook"
   ```

Useful endpoints:

- `GET /telegram/me`
- `POST /telegram/commands`
- `POST /telegram/webhook/delete`

Do not commit real bot tokens. If a token was pasted in chat or committed, rotate it in BotFather.
