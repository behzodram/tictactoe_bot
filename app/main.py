import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random
import time
import logging
import config 

# Logging sozlash
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Bot tokenini o'rnating (Buni @BotFather dan oling)
TOKEN = config.BOT_TOKEN  # Bu yerga o'z tokeningizni qo'ying

try:
    bot = telebot.TeleBot(TOKEN)
    logger.info("Bot obyekti yaratildi")
except Exception as e:
    logger.error(f"Bot yaratishda xato: {e}")
    exit(1)

# O'yin ma'lumotlarini saqlash uchun dictionary
games = {}

# O'yin holatini saqlash klassi
class TicTacToeGame:
    def __init__(self, chat_id, player1_id, player2_id=None):
        self.chat_id = chat_id
        self.board = [' ' for _ in range(9)]
        self.player1 = player1_id
        self.player2 = player2_id
        self.current_player = player1_id
        self.player_symbols = {player1_id: '❌', player2_id: '⭕' if player2_id else '⭕'}
        self.game_mode = 'vs_human' if player2_id else 'vs_bot'
        self.winner = None
        self.game_over = False
        self.message_id = None
    
    def make_move(self, position, player_id):
        if self.game_over or self.current_player != player_id:
            return False
        
        if self.board[position] == ' ':
            self.board[position] = self.player_symbols[player_id]
            
            # G'olibni tekshirish
            self.check_winner()
            
            # O'yinchi almashish
            if not self.game_over:
                if self.game_mode == 'vs_bot' and player_id == self.player1:
                    time.sleep(0.5)  # Bot o'ylayotgandek qilish uchun
                    self.bot_move()
                else:
                    self.current_player = self.player2 if self.current_player == self.player1 else self.player1
            
            return True
        return False
    
    def bot_move(self):
        # Oddiy bot logikasi: bo'sh katakni tanlaydi
        available_positions = [i for i, cell in enumerate(self.board) if cell == ' ']
        if available_positions:
            position = random.choice(available_positions)
            self.board[position] = self.player_symbols[self.player2]
            self.check_winner()
            if not self.game_over:
                self.current_player = self.player1
    
    def check_winner(self):
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Gorizontal
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Vertikal
            [0, 4, 8], [2, 4, 6]              # Diagonal
        ]
        
        for combo in winning_combinations:
            if (self.board[combo[0]] != ' ' and 
                self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]]):
                self.game_over = True
                # G'olibni aniqlash
                symbol = self.board[combo[0]]
                self.winner = self.player1 if symbol == self.player_symbols[self.player1] else self.player2
                return
        
        # Durrangni tekshirish
        if ' ' not in self.board:
            self.game_over = True
    
    def get_board_display(self):
        # Doskani yanada chiroyli qilish
        board_display = []
        for i in range(0, 9, 3):
            row = []
            for j in range(3):
                cell = self.board[i + j]
                if cell == ' ':
                    row.append(f"({i+j+1})")
                else:
                    row.append(cell)
            board_display.append(" ".join(row))
        
        return "\n".join(board_display)

# /start komandasi
@bot.message_handler(commands=['start'])
def send_welcome(message):
    try:
        welcome_text = """
🎮 *Tic Tac Toe Botga Xush Kelibsiz!*

*Buyruqlar:*
/start - Botni ishga tushirish
/newgame - Yangi o'yin boshlash
/help - Yordam

Bot bilan o'ynash uchun /newgame buyrug'ini bering!
        """
        bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown')
        logger.info(f"/start command from user {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in /start: {e}")

# /help komandasi
@bot.message_handler(commands=['help'])
def send_help(message):
    try:
        help_text = """
*Qanday o'ynash kerak:*

1. /newgame - yangi o'yinni boshlash
2. O'yin rejimini tanlang:
   - Kompyuterga qarshi
   - Do'stingizga qarshi
3. Doskaning raqamli tugmalarini bosing

*Qoidalar:*
- 3x3 katakchalar doskasi
- ❌ va ⭕ belgilari
- Birinchi ketma-ket 3 ta belgi qo'ygan g'olib bo'ladi

*Raqamlar tartibi:*
(1) (2) (3)
(4) (5) (6)
(7) (8) (9)
        """
        bot.send_message(message.chat.id, help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in /help: {e}")

# /newgame komandasi
@bot.message_handler(commands=['newgame'])
def new_game(message):
    try:
        chat_id = message.chat.id
        player_id = message.from_user.id
        
        # Avvalgi o'yinni tozalash
        if chat_id in games:
            del games[chat_id]
        
        # O'yin rejimini tanlash uchun tugmalar
        markup = InlineKeyboardMarkup(row_width=2)
        markup.add(
            InlineKeyboardButton("🤖 Kompyuterga qarshi", callback_data="mode_vs_bot"),
            InlineKeyboardButton("👥 Do'stingizga qarshi", callback_data="mode_vs_human")
        )
        
        bot.send_message(chat_id, "O'yin rejimini tanlang:", reply_markup=markup)
        logger.info(f"New game started by user {player_id}")
    except Exception as e:
        logger.error(f"Error in /newgame: {e}")

# /join komandasi
@bot.message_handler(commands=['join'])
def join_game(message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        
        # O'yin qidirish
        game_found = None
        for game_chat_id, game in games.items():
            if game.game_mode == 'vs_human' and game.player2 is None and game.player1 != user_id:
                game_found = game
                break
        
        if game_found:
            game_found.player2 = user_id
            game_found.player_symbols[user_id] = '⭕'
            send_game_board(chat_id, game_found)
            logger.info(f"User {user_id} joined game in chat {chat_id}")
        else:
            bot.send_message(chat_id, "Hozircha ochiq o'yinlar yo'q. /newgame bilan yangi o'yin boshlang.")
    except Exception as e:
        logger.error(f"Error in /join: {e}")

# Callback query handler
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        chat_id = call.message.chat.id
        user_id = call.from_user.id
        
        if call.data.startswith("mode_"):
            handle_game_mode(call, chat_id, user_id)
        
        elif call.data.startswith("join_"):
            handle_join_game(call, chat_id, user_id)
        
        elif call.data.startswith("move_"):
            handle_player_move(call, chat_id, user_id)
        
        elif call.data == "restart":
            handle_restart(call, chat_id)
        
        elif call.data.startswith("blocked_"):
            bot.answer_callback_query(call.id, "Bu katak band!")
    
    except Exception as e:
        logger.error(f"Error in callback query: {e}")
        try:
            bot.answer_callback_query(call.id, "Xato yuz berdi. Iltimos, qayta urinib ko'ring.")
        except:
            pass

def handle_game_mode(call, chat_id, user_id):
    """O'yin rejimini tanlash"""
    if call.data == "mode_vs_bot":
        game = TicTacToeGame(chat_id, user_id)
        games[chat_id] = game
        send_game_board(chat_id, game)
        
    elif call.data == "mode_vs_human":
        # 2-o'yinchini kutilayotgan holat
        game = TicTacToeGame(chat_id, user_id)
        games[chat_id] = game
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🎮 O'yiniga qo'shilish", callback_data=f"join_{user_id}_{chat_id}"))
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=call.message.message_id,
            text=f"O'yinchi 1: {call.from_user.first_name}\nO'yinchi 2: Kutilyapti...\n\nIkkinchi o'yinchi 'O'yiniga qo'shilish' tugmasini bosing.",
            reply_markup=markup
        )

def handle_join_game(call, chat_id, user_id):
    """O'yinga qo'shilish"""
    try:
        parts = call.data.split("_")
        if len(parts) >= 3:
            creator_id = int(parts[1])
            target_chat_id = int(parts[2]) if len(parts) > 2 else chat_id
            
            if creator_id != user_id:
                if target_chat_id in games:
                    game = games[target_chat_id]
                    if game.game_mode == 'vs_human' and game.player2 is None:
                        game.player2 = user_id
                        game.player_symbols[user_id] = '⭕'
                        send_game_board(target_chat_id, game)
                        bot.answer_callback_query(call.id, "O'yinga qo'shildingiz!")
                    else:
                        bot.answer_callback_query(call.id, "Bu o'yin allaqachon boshlangan!")
                else:
                    bot.answer_callback_query(call.id, "O'yin topilmadi!")
            else:
                bot.answer_callback_query(call.id, "Siz o'z o'yiningizga qo'shila olmaysiz!")
    except Exception as e:
        logger.error(f"Error in handle_join_game: {e}")
        bot.answer_callback_query(call.id, "Xato yuz berdi!")

def handle_player_move(call, chat_id, user_id):
    """O'yinchi harakati"""
    position = int(call.data.split("_")[1])
    
    if chat_id in games:
        game = games[chat_id]
        
        if game.make_move(position, user_id):
            if game.game_over:
                send_game_result(chat_id, game)
                if chat_id in games:
                    del games[chat_id]
            else:
                send_game_board(chat_id, game)
        else:
            bot.answer_callback_query(call.id, "Bu katak band yoki sizning navbatingiz emas!")
    else:
        bot.answer_callback_query(call.id, "O'yin topilmadi!")

def handle_restart(call, chat_id):
    """O'yinni qayta boshlash"""
    if chat_id in games:
        del games[chat_id]
    new_game(call.message)

# O'yin doskasini yuborish
def send_game_board(chat_id, game):
    try:
        board = game.get_board_display()
        
        # Tugmalar doskasi
        markup = InlineKeyboardMarkup(row_width=3)
        
        # 3x3 tugmalar
        for i in range(0, 9, 3):
            row_buttons = []
            for j in range(3):
                cell_index = i + j
                if game.board[cell_index] == ' ':
                    row_buttons.append(InlineKeyboardButton(f"{cell_index+1}", callback_data=f"move_{cell_index}"))
                else:
                    row_buttons.append(InlineKeyboardButton(game.board[cell_index], callback_data=f"blocked_{cell_index}"))
            markup.add(*row_buttons)
        
        # Qo'shimcha tugmalar
        markup.row(
            InlineKeyboardButton("🔄 Yangi o'yin", callback_data="restart"),
            InlineKeyboardButton("❌ O'yinni tugatish", callback_data="cancel")
        )
        
        # O'yinchi ma'lumotlari
        player1_name = "Siz" if game.current_player == game.player1 else "Raqib"
        player2_name = "Siz" if game.current_player == game.player2 else "Raqib"
        
        if game.game_mode == 'vs_bot':
            status = f"❌ Siz vs 🤖 Bot"
            if game.current_player == game.player1:
                turn_text = "✅ *Sizning navbatingiz!*"
            else:
                turn_text = "🤖 *Bot o'ylayapti...*"
        else:
            status = f"❌ {player1_name} vs ⭕ {player2_name}"
            if game.current_player == game.player1:
                turn_text = "✅ *❌ belgisining navbati*"
            else:
                turn_text = "✅ *⭕ belgisining navbati*"
        
        message_text = f"*Tic Tac Toe*\n\n{board}\n\n{status}\n\n{turn_text}"
        
        # Xabarni yangilash yoki yangisini yuborish
        if game.message_id:
            try:
                msg = bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=game.message_id,
                    text=message_text,
                    reply_markup=markup,
                    parse_mode='Markdown'
                )
            except:
                msg = bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode='Markdown')
                game.message_id = msg.message_id
        else:
            msg = bot.send_message(chat_id, message_text, reply_markup=markup, parse_mode='Markdown')
            game.message_id = msg.message_id
            
    except Exception as e:
        logger.error(f"Error in send_game_board: {e}")

# O'yin natijasini yuborish
def send_game_result(chat_id, game):
    try:
        board = game.get_board_display()
        
        if game.winner:
            if game.game_mode == 'vs_bot':
                if game.winner == game.player1:
                    result_text = "🎉 *Tabriklayman! Siz yutdingiz!* 🏆"
                else:
                    result_text = "🤖 *Bot yutdi! Keyingi safar omad!*"
            else:
                winner_name = "Siz" if game.winner == game.chat_id else "Raqib"
                result_text = f"🎉 *{winner_name} yutdi! Tabriklayman!* 🏆"
        else:
            result_text = "🤝 *Durrang! Hech kim yutmadi!*"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🔄 Yangi o'yin", callback_data="restart"))
        
        bot.send_message(chat_id, f"*O'yin tugadi!*\n\n{board}\n\n{result_text}", 
                        reply_markup=markup, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in send_game_result: {e}")

# Xatolikni ushlash uchun handler
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, "Men faqat Tic Tac Toe o'yinini o'ynayman. /help buyrug'i bilan yordam oling.")

# Botni ishga tushirish
if __name__ == '__main__':
    logger.info("Bot ishga tushirilmoqda...")
    
    # Token tekshirish
    if TOKEN == 'YOUR_BOT_TOKEN_HERE':
        logger.error("Iltimos, bot tokeningizni TOKEN o'zgaruvchisiga qo'ying!")
        print("=" * 60)
        print("DIQQAT: Bot tokenini o'zgartirishingiz kerak!")
        print("1. @BotFather ga boring")
        print("2. Yangi bot yarating yoki mavjud bot tokenni oling")
        print("3. TOKEN = 'YOUR_BOT_TOKEN_HERE' o'rniga tokenni qo'ying")
        print("=" * 60)
        exit(1)
    
    try:
        # Bot ma'lumotlarini tekshirish
        bot_info = bot.get_me()
        logger.info(f"Bot muvaffaqiyatli ulandi: @{bot_info.username}")
        logger.info(f"Bot ismi: {bot_info.first_name}")
        
        print("\n" + "=" * 60)
        print(f"🤖 Bot: @{bot_info.username}")
        print(f"📛 Ism: {bot_info.first_name}")
        print("✅ Bot muvaffaqiyatli ishga tushdi!")
        print("📱 Telegramda botni qidiring va /start bosing")
        print("=" * 60 + "\n")
        
        # Botni ishga tushirish
        bot.polling(none_stop=True, interval=2, timeout=30)
        
    except telebot.apihelper.ApiException as e:
        logger.error(f"Telegram API xatosi: {e}")
        print("\n❌ XATO: Telegram API ga ulanib bo'lmadi.")
        print("Sabablari:")
        print("1. Noto'g'ri bot token")
        print("2. Internet aloqasi muammosi")
        print("3. Bot bloklangan yoki o'chirilgan")
        print("\nTokenni tekshiring: @BotFather")
        
    except Exception as e:
        logger.error(f"Umumiy xato: {e}")
        print(f"\n❌ XATO: {e}")