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
    "1": {"name": "Khormaye Mazafati", "price": 0, "unit": "kilo"},
    "2": {"name": "Keshmesh Sabz", "price": 0, "unit": "kilo"},
    "3": {"name": "Khormaye Kabkab", "price": 0, "unit": "kilo"},
    "4": {"name": "Khormaye Piyaram", "price": 0, "unit": "kilo"},
    "5": {"name": "Toot Khoshk", "price": 0, "unit": "kilo"},
}
logging.basicConfig(level=logging.INFO)
user_orders = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[KeyboardButton("Order")],[KeyboardButton("Products"), KeyboardButton("Contact")],[KeyboardButton("Help")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Welcome to Asadpour Dry Fruits!\n\nFresh dates directly from garden\nVacuum packaging\nShipping all over Iran\nMinimum order 1 kg\n\nChoose an option:", reply_markup=reply_markup)

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "Product List:\n\n"
    for key, product in PRODUCTS.items():
        price_text = f"{product['price']:,} Toman" if product['price'] > 0 else "Contact us"
        text += f"{key}. {product['name']} - {price_text} per {product['unit']}\n"
    text += "\nVacuum packaging\nMinimum 1 kg\nShipping all over Iran"
    await update.message.reply_text(text)

async def contact_us(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Contact Asadpour Dry Fruits\n\nAbbas Asadpour\nSaturday to Thursday: 8am to 9pm\n\nShipping:\nUnder 20kg: buyer pays shipping\n20kg and above: free shipping\nShipping all over Iran")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("How to order:\n1. Press Order\n2. Choose product\n3. Enter weight\n4. Enter delivery info\n5. Pay to card\n6. Send receipt photo\n7. Order confirmed")

async def start_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = []
    for key, product in PRODUCTS.items():
        price_text = f" - {product['price']:,}" if product['price'] > 0 else ""
        keyboard.append([InlineKeyboardButton(f"{product['name']}{price_text}", callback_data=f"product_{key}")])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    await update.message.reply_text("Which product do you want?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSE_PRODUCT

async def choose_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Order cancelled.")
        return ConversationHandler.END
    product_key = query.data.replace("product_", "")
    product = PRODUCTS[product_key]
    user_orders[query.from_user.id] = {"product_key": product_key, "product": product}
    await query.edit_message_text(f"Product: {product['name']}\n\nHow many kg? (example: 3)")
    return CHOOSE_WEIGHT

async def choose_weight(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        weight = float(update.message.text.replace(",", "."))
        if weight <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Please enter a number. Example: 2")
        return CHOOSE_WEIGHT
    user_id = update.message.from_user.id
    order = user_orders[user_id]
    order["weight"] = weight
    product = order["product"]
    if product["price"] > 0:
        total = product["price"] * weight
        order["total"] = total
        price_text = f"Amount: {total:,.0f} Toman\n"
    else:
        price_text = "Price will be confirmed later\n"
        order["total"] = 0
    await update.message.reply_text(f"Weight: {weight} kg\n{price_text}\nEnter your full name:")
    return GET_NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("Please enter your full name.")
        return GET_NAME
    user_orders[update.message.from_user.id]["name"] = name
    await update.message.reply_text(f"Name: {name}\n\nEnter your phone number:")
    return GET_PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip().replace("-", "").replace(" ", "")
    if len(phone) < 10:
        await update.message.reply_text("Please enter a valid phone number. Example: 09123456789")
        return GET_PHONE
    user_orders[update.message.from_user.id]["phone"] = phone
    await update.message.reply_text(f"Phone: {phone}\n\nEnter your full address:")
    return GET_ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    address = update.message.text.strip()
    if len(address) < 10:
        await update.message.reply_text("Please enter a more complete address.")
        return GET_ADDRESS
    user_id = update.message.from_user.id
    order = user_orders[user_id]
    order["address"] = address
    product = order["product"]
    weight = order["weight"]
    total = order.get("total", 0)
    shipping = "Free shipping!" if weight >= 20 else "Shipping cost paid by buyer"
    payment_text = f"Amount: {total:,.0f} Toman" if total > 0 else "Amount will be confirmed"
    await update.message.reply_text(f"Order Summary:\n\nProduct: {product['name']}\nWeight: {weight} kg\nName: {order['name']}\nPhone: {order['phone']}\nAddress: {address}\n\n{shipping}\n{payment_text}\n\nPayment Info:\nBank: {CARD_BANK}\nCard: {CARD_NUMBER}\nName: {CARD_NAME}\n\nPlease send receipt photo after payment.")
    return GET_RECEIPT

async def get_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    order = user_orders.get(user_id, {})
    if not update.message.photo:
        await update.message.reply_text("Please send a photo of your payment receipt.")
        return GET_RECEIPT
    if ADMIN_CHAT_ID:
        product = order.get("product", {})
        total = order.get("total", 0)
        total_text = f"{total:,.0f} Toman" if total > 0 else "Pending"
        caption = f"NEW ORDER\n\nProduct: {product.get('name', '-')}\nWeight: {order.get('weight', '-')} kg\nAmount: {total_text}\nName: {order.get('name', '-')}\nPhone: {order.get('phone', '-')}\nAddress: {order.get('address', '-')}\nUser: @{update.message.from_user.username or 'none'}"
        await context.bot.send_photo(chat_id=ADMIN_CHAT_ID, photo=update.message.photo[-1].file_id, caption=caption)
    await update.message.reply_text("Your order has been registered!\nWill be confirmed within 2 hours.\nThank you!")
    if user_id in user_orders:
        del user_orders[user_id]
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_orders:
        del user_orders[user_id]
    await update.message.reply_text("Order cancelled.")
    return ConversationHandler.END

async def set_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global ADMIN_CHAT_ID
    ADMIN_CHAT_ID = update.message.chat_id
    await update.message.reply_text(f"You are now admin! ID: {ADMIN_CHAT_ID}")

def main():
    app = Application.builder().token(TOKEN).build()
    conv_handler = ConversationHandler(
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
    app.add_handler(conv_handler)
    app.add_handler(MessageHandler(filters.Regex("^Products$"), show_products))
    app.add_handler(MessageHandler(filters.Regex("^Contact$"), contact_us))
    app.add_handler(MessageHandler(filters.Regex("^Help$"), help_command))
    print("Bot started!")
    app.run_polling()

if __name__ == "__main__":
    main()
