import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

TOKEN = "8944172746:AAEfxxdztcV3ccxPs-9f7TvK86yrN79fCu8"
ADMIN_CHAT_ID = None
CARD_NUMBER = "6219-8619-9707-5451"
CARD_NAME = "Abbas Asadpour"
CARD_BANK = "Bank Saman"
CHOOSE_PRODUCT, CHOOSE_WEIGHT, GET_NAME, GET_PHONE, GET_ADDRESS, GET_RECEIPT = range(6)
PRODUCTS = {
    "1": {"name": "Khormaye Mazafati", "price": 0},
    "2": {"name": "Keshmesh Sabz", "price": 0},
    "3": {"name": "Khormaye Kabkab", "price": 0},
    "4": {"name": "Khormaye Piyaram", "price": 0},
    "5": {"name": "Toot Khoshk", "price": 0},
}
logging.basicConfig(level=logging.INFO)
user_orders = {}

async def start(update, context):
    keyboard = [[KeyboardButton("Order")],[KeyboardButton("Products"), KeyboardButton("Contact")],[KeyboardButton("Help")]]
    await update.message.reply_text("Welcome to Asadpour Dry Fruits!\n\nFresh dates from garden\nVacuum packaging\nShipping all over Iran\nMinimum 1 kg\n\nChoose:", reply_markup=ReplyKeyboardMarkup(keyboard, resize_keyboard=True))

async def show_products(update, context):
    text = "Products:\n\n"
    for key, p in PRODUCTS.items():
        price = f"{p['price']:,} T" if p['price'] > 0 else "Contact us"
        text += f"{key}. {p['name']} - {price}/kg\n"
    text += "\nVacuum packaging | Min 1kg | All Iran"
    await update.message.reply_text(text)

async def contact_us(update, context):
    await update.message.reply_text("Asadpour Dry Fruits\nAbbas Asadpour\nSat-Thu: 8am-9pm\n\nShipping:\nUnder 20kg: buyer pays\n20kg+: free shipping")

async def help_cmd(update, context):
    await update.message.reply_text("How to order:\n1. Press Order\n2. Choose product\n3. Enter weight\n4. Enter info\n5. Pay to card\n6. Send receipt\n7. Confirmed!")

async def start_order(update, context):
    keyboard = [[InlineKeyboardButton(p['name'], callback_data=f"p_{k}")] for k, p in PRODUCTS.items()]
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    await update.message.reply_text("Which product?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_PRODUCT

async def choose_product(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Cancelled.")
        return ConversationHandler.END
    key = query.data.replace("p_", "")
    product = PRODUCTS[key]
    user_orders[query.from_user.id] = {"product": product}
    await query.edit_message_text(f"Product: {product['name']}\n\nHow many kg? (example: 3)")
    return CHOOSE_WEIGHT

async def choose_weight(update, context):
    try:
        weight = float(update.message.text.replace(",", "."))
        if weight <= 0:
            raise ValueError
    except:
        await update.message.reply_text("Enter a number. Example: 2")
        return CHOOSE_WEIGHT
    order = user_orders[update.message.from_user.id]
    order["weight"] = weight
    p = order["product"]
    total = p['price'] * weight if p['price'] > 0 else 0
    order["total"] = total
    price_text = f"Amount: {total:,.0f} T" if total > 0 else "Price TBD"
    await update.message.reply_text(f"Weight: {weight}kg\n{price_text}\n\nYour full name:")
    return GET_NAME

async def get_name(update, context):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("Enter full name.")
        return GET_NAME
    user_orders[update.message.from_user.id]["name"] = name
    await update.message.reply_text(f"Name: {name}\n\nPhone number:")
    return GET_PHONE

async def get_phone(update, context):
    phone = update.message.text.strip().replace("-","").replace(" ","")
    if len(phone) < 10:
        await update.message.reply_text("Valid phone please. Example: 09123456789")
        return GET_PHONE
    user_orders[update.message.from_user.id]["phone"] = phone
    await update.message.reply_text(f"Phone: {phone}\n\nFull address:")
    return GET_ADDRESS

async def get_address(update, context):
    address = update.message.text.strip()
    if len(address) < 10:
        await update.message.reply_text("More complete address please.")
        return GET_ADDRESS
    uid = update.message.from_user.id
    order = user_orders[uid]
    order["address"] = address
    p = order["product"]
    w = order["weight"]
    total = order.get("total", 0)
    shipping = "Free shipping!" if w >= 20 else "Buyer pays shipping"
    amount = f"Amount: {total:,.0f} T" if total > 0 else "Amount TBD"
    await update.message.reply_text(
        f"Order Summary:\nProduct: {p['name']}\nWeight: {w}kg\nName: {order['name']}\nPhone: {order['phone']}\nAddress: {address}\n\n{shipping}\n{amount}\n\nPayment:\nBank: {CARD_BANK}\nCard: {CARD_NUMBER}\nName: {CARD_NAME}\n\nSend receipt photo after payment."
    )
    return GET_RECEIPT

async def get_receipt(update, context):
    uid = update.message.from_user.id
    order = user_orders.get(uid, {})
    if not update.message.photo:
        await update.message.reply_text("Send receipt photo.")
        return GET_RECEIPT
    global ADMIN_CHAT_ID
    if ADMIN_CHAT_ID:
        p = order.get("product", {})
        total = order.get("total", 0)
        caption = f"NEW ORDER\nProduct: {p.get('name','-')}\nWeight: {order.get('weight','-')}kg\nAmount: {total:,.0f}T\nName: {order.get('name','-')}\nPhone: {order.get('phone','-')}\nAddress: {order.get('address','-')}\nUser: @{update.message.from_user.username or 'none'}"
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=caption)
    await update.message.reply_text("Order registered!\nConfirmed within 2 hours. Thank you!")
    user_orders.pop(uid, None)
    return ConversationHandler.END

async def cancel(update, context):
    user_orders.pop(update.message.from_user.id, None)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END

async def set_admin(update, context):
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = update.message.chat_id
    await update.message.reply_text(f"You are admin! ID: {ADMIN_CHAT_ID}")

def main():
    app = Application.builder().token(TOKEN).build()
    conv = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Order$"), start_order)],
        states={
            CHOOSE_PRODUCT: [CallbackQueryHandler(choose_product)],
            CHOOSE_WEIGHT: [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_weight)],
            GET_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            GET_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            GET_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            GET_RECEIPT: [MessageHandler(filters.PHOTO, get_receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", set_admin))
    app.add_handler(conv)
    app.add_handler(MessageHandler(filters.Regex("^Products$"), show_products))
    app.add_handler(MessageHandler(filters.Regex("^Contact$"), contact_us))
    app.add_handler(MessageHandler(filters.Regex("^Help$"), help_cmd))
    print("Bot started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
