from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import asyncio
import os

# Simple in-memory storage (good enough for personal use; survives restarts on Render free tier)
accounts = {}  # format: {"WH123": "2026-01-01"}

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 2:
        await update.message.reply_text("Usage: /add <username> <YYYY-MM-DD>")
        return
    
    username = context.args[0].upper()
    try:
        add_date = datetime.strptime(context.args[1], "%Y-%m-%d").date()
    except ValueError:
        await update.message.reply_text("Date must be YYYY-MM-DD format")
        return
    
    accounts[username] = add_date.strftime("%Y-%m-%d")
    await update.message.reply_text(f"Added {username} — added on {add_date}. Will alert in 14 days.")

async def list_accounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not accounts:
        await update.message.reply_text("No accounts tracked yet.")
        return
    
    message = "*Active William Hill Accounts*\n\n"
    today = datetime.today().date()
    for username, date_str in accounts.items():
        add_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        days_left = (add_date + timedelta(days=14) - today).days
        message += f"{username} — Added: {date_str} — {days_left} days until alert\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def daily_check(context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today().date()
    to_alert = []
    
    for username, date_str in list(accounts.items()):
        add_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        if add_date + timedelta(days=14) == today:
            to_alert.append(username)
            # Optional: remove after alert
            # del accounts[username]
    
    if to_alert:
        chat_id = context.job.data['chat_id']
        message = "*14-DAY ALERT — TIME TO WITHDRAW*\n\n"
        for username in to_alert:
            message += f"• {username}\n"
        message += "\nWithdraw and rotate these accounts now!"
        await context.bot.send_message(chat_id=chat_id, text=message, parse_mode='Markdown')

def main():
    token = os.getenv("BOT_TOKEN")
    if not token:
        print("Error: BOT_TOKEN not set")
        return
    
    app = ApplicationBuilder().token(token).build()
    
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("list", list_accounts))
    
    # Daily check at 9:00 AM UTC (adjust if you want different time)
    jq = app.job_queue
    jq.run_daily(
        daily_check,
        time=datetime.strptime("09:00", "%H:%M").time(),
        data={'chat_id': gdaviez}  # Replace with your Telegram user ID
    )
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
