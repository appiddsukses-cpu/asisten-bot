# bot.py - Asisten Hidup Bot
import sqlite3
import os
import datetime as dt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (Application, CommandHandler, CallbackQueryHandler,
                          MessageHandler, filters, ContextTypes)

TOKEN = os.getenv("BOT_TOKEN", "PASTE_TOKEN_BOTFATHER_ANDA_DI_SINI")
WIB = dt.timezone(dt.timedelta(hours=7))

def db():
    conn = sqlite3.connect("data.db")
    conn.execute("""CREATE TABLE IF NOT EXISTS reminder(
        user_id INTEGER, jenis TEXT, nama TEXT, tempo TEXT)""")
    return conn

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🚗 Pajak Kendaraan",  callback_data="pajak")],
        [InlineKeyboardButton("📱 Garansi Elektronik", callback_data="garansi")],
        [InlineKeyboardButton("🪪 Perpanjangan SIM",  callback_data="sim")],
    ]
    await update.message.reply_text(
        "👋 Halo! Saya Asisten Hidup Bot.\n"
        "Saya mengingatkan Anda SEBELUM pajak kendaraan, garansi elektronik, "
        "atau SIM Anda habis masa berlaku. 100% Gratis!\n\nPilih layanan:",
        reply_markup=InlineKeyboardMarkup(kb))

async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    nama_menu = {"pajak": "🚗 Pajak Kendaraan",
                 "garansi": "📱 Garansi Elektronik",
                 "sim": "🪪 Perpanjangan SIM"}[q.data]
    ctx.user_data["jenis"] = q.data
    await q.edit_message_text(
        f"{nama_menu}\n\nKetik keterangan dan tanggal jatuh tempo "
        "(format YYYY-MM-DD).\nContoh:\n"
        "Motor Vario B 1234 CD\n2026-12-01")

async def terima_pesan(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "jenis" not in ctx.user_data:
        await start(update, ctx)
        return
    baris = update.message.text.strip().split("\n")
    tempo = baris[-1].strip()
    nama  = " ".join(baris[:-1]) or "-"
    conn = db()
    conn.execute("INSERT INTO reminder VALUES (?,?,?,?)",
                 (update.effective_user.id, ctx.user_data["jenis"], nama, tempo))
    conn.commit(); conn.close()
    await update.message.reply_text(
        f"✅ Tersimpan!\n📌 {nama}\n📅 Jatuh tempo: {tempo}\n"
        "Saya akan mengingatkan Anda 7 hari sebelumnya. 🔔")

async def terima_foto(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📸 Fitur baca foto otomatis (AI) segera hadir!\n"
        "Untuk sekarang, ketik manual seperti contoh ya. "
        "Ingat: jangan kirim foto berisi NIK/alamat tanpa dicoret dulu. 🙏")

async def pengingat_harian(ctx: ContextTypes.DEFAULT_TYPE):
    target = (dt.datetime.now(WIB) + dt.timedelta(days=7)).strftime("%Y-%m-%d")
    conn = db()
    rows = conn.execute(
        "SELECT user_id, jenis, nama, tempo FROM reminder WHERE tempo=?",
        (target,)).fetchall()
    conn.close()
    for uid, jenis, nama, tempo in rows:
        await ctx.bot.send_message(
            uid,
            f"🔔 PENGINGAT: {nama} akan jatuh tempo pada {tempo} (7 hari lagi)!\n"
            "Mau dibantu urus tanpa antri? Hubungi mitra kami: wa.me/62812xxxxxxx")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu))
    app.add_handler(MessageHandler(filters.PHOTO, terima_foto))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, terima_pesan))
    app.job_queue.run_daily(pengingat_harian, time=dt.time(8, 0, tzinfo=WIB))
    print("Bot berjalan...")
    app.run_polling()

main()
