import csv
from datetime import datetime, timedelta
from typing import List, Dict
from user import User
from telebot import TeleBot
from telebot.types import Message

TODAY = datetime.now().strftime('%d.%m.%Y')
bot = TeleBot("7321495529:AAGuB45qmPioQO9gO5LIFgwdlRCW8qzBvlo")

def get_username_from_msg(message: Message) -> str:
    lastname = message.from_user.last_name or message.from_user.username or f"{message.from_user.id}"
    return f"{message.from_user.first_name}-{lastname}"

                    
def readUsersFromCsv(file_path: str = 'data.csv') -> List[User]:
    """Read users from a CSV file"""
    users = []
    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file, delimiter=';')
        for row in csv_reader:
            name = row['Name']
            totalScore = int(row['Total Score'])
            days = {
                datetime.strptime(date, '%d.%m.%Y'): int(score) if score else 0
                for date, score in row.items() if date not in ['Name', 'Total Score']
            }
            user = User(name, totalScore, days)
            users.append(user)
    return users



def findUserByName(users: List[User], name: str) -> User:
    """Find user by name"""
    for user in users:
        if user.name == name:
            return user
    return None


def createUser(users: List[User], name: str, totalScore: int, scores: Dict[str, int]) -> None:
    """Create a new user"""
    days = {datetime.strptime(date, '%d.%m.%Y'): score for date, score in scores.items()}
    new_user = User(name, totalScore, days)
    users.append(new_user)


def writeUsers2Csv(file_path: str, users: List[User]) -> None:
    """Write users to a CSV file"""
    if not users:
        return

    # Collect all dates present in users' records
    all_dates = set()
    for user in users:
        all_dates.update(user.days.keys())
    dateStrs = sorted([date.strftime('%d.%m.%Y') for date in all_dates])

    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')

        # Write header
        header = ['Name', 'Total Score'] + dateStrs
        writer.writerow(header)

        # Write user data
        for user in users:
            row = [user.name, user.totalScore] + [user.days.get(datetime.strptime(date_str, '%d.%m.%Y'), '') for
                                                  date_str in dateStrs]
            writer.writerow(row)


def addMissingDates(users: List[User], end_date_str: str) -> None:
    """Add missing dates for all users up to the specified end date"""
    end_date = datetime.strptime(end_date_str, '%d.%m.%Y')
    for user in users:
        if user.days:
            start_date = max(user.days.keys())
        else:
            start_date = min(user.days.keys())

        current_date = start_date + timedelta(days=1)
        while current_date <= end_date:
            user.days[current_date] = 0
            current_date += timedelta(days=1)


def checkCharacterInList(message: str, allowedChars: List[str]) -> bool:
    """Check if all characters in the message are in the allowed character list"""
    return all(char in allowedChars for char in message)


def calculatePoints(letter: str, position: int) -> int:
    """Calculate points for a given letter based on its position"""
    # Base point values according to letter's position
    position_points = {
        1: 5,
        2: 3,
        3: 3,
        4: 3,
        5: 4
    }

    # For letter 'x', always return 0
    if letter == 'x' or letter == 'X':
        return 0

    # Get the base points based on the letter's position
    base_points = position_points.get(position, 0)

    # If letter is 'e', use the base point directly
    if letter == 'e' or letter == 'E':
        return base_points

    # If letter is 'c', multiply the base points by 2
    if letter == 'c' or letter == 'C':
        return base_points * 2

    # For any other letter, return the base point value
    return base_points


def displayUsers(users: List[User]) -> None:
    """Display all users"""
    for user in users:
        print(user)


@bot.message_handler(commands=['start'])
def handle_start(message):
    bot.reply_to(message, "Welcome! Use /score <name> <date> to find a user's score or send a message to evaluate it.")

@bot.message_handler(commands=['skorum'])
def handle_skoryeni(message: Message):
    if message.from_user is not None:

        username = get_username_from_msg(message)

        today = datetime.now().strftime('%d.%m.%Y')

        # Load users from CSV
        users = readUsersFromCsv('data.csv')

        # Find the user
        user = findUserByName(users, username)

        if user:
            # Get today's score
            score = user.days.get(datetime.strptime(today, '%d.%m.%Y'), 0)
            bot.reply_to(message, f"Bugünkü skorunuz: {score} puan")
        else:
            bot.reply_to(message, "Kullanıcı bulunamadı.")
    else:
        bot.reply_to(message, "HATA: Kullanıcı bulunamadı")

@bot.message_handler(commands=['skor'])
def handle_score(message: Message):
    try:
        _, name, date = message.text.split()
        users = readUsersFromCsv('data.csv')
        user = findUserByName(users, name)
        if user:
            date_obj = datetime.strptime(date, '%d.%m.%Y')
            score = user.days.get(date_obj)
            if score is not None:
                bot.reply_to(message, f"{user.name} kullanıcısının {date} tarihli skoru: {score}")
            else:
                bot.reply_to(message, f"{user.name} kullanıcısı için {date} tarihinde skor bulunamadı.")
        else:
            bot.reply_to(message, f"kullanıcı {name} bulunamadı.")
    except ValueError:
        bot.reply_to(message, "Kullanım: /skor <Telegram kullanıcı adın> <Tarih>")


@bot.message_handler(commands=['tablo'])
def handle_csv_request(message: Message):
    """Send the CSV data file to the user."""
    try:
        # Define the file path
        file_path = 'data.csv'

        # Send the file to the user
        with open(file_path, 'rb') as file:
            bot.send_document(message.chat.id, file, caption="Buyrunuz! Anlık Skor Tablosu CSV formatında:")

    except Exception as e:
        bot.reply_to(message, f"An error occurred: {e}")

@bot.message_handler(content_types=['document'])
def handle_csv_upload(message: Message):
    try:
        # Gönderilen dosya bir CSV mi kontrol et
        if message.document.mime_type == 'text/csv':
            file_info = bot.get_file(message.document.file_id)
            downloaded_file = bot.download_file(file_info.file_path)

            # Yeni dosyayı 'uploaded_data.csv' olarak kaydet
            with open('uploaded_data.csv', 'wb') as new_file:
                new_file.write(downloaded_file)

            # Yeni dosyayı oku
            with open('uploaded_data.csv', 'r') as file:
                csv_reader = csv.reader(file, delimiter=';')
                data = list(csv_reader)

            # Eski CSV dosyasını aç ve içini temizle
            with open('data.csv', 'w', newline='') as existing_file:
                csv_writer = csv.writer(existing_file, delimiter=';')

                # Yeni dosyanın içeriğini eski dosyaya yaz
                csv_writer.writerows(data)

            # Bilgilendirme mesajı
            bot.reply_to(message, "Yeni CSV dosyası başarıyla yüklendi ve eski dosyanın yerine yazıldı.")
        else:
            bot.reply_to(message, "Lütfen bir CSV dosyası gönderin.")

    except Exception as e:
        bot.reply_to(message, f"Hata oluştu: {e}")


def evaluateMessage(message: str) -> int:
    """Evaluate the total points for a message"""
    # Define allowed characters
    allowedChars = {'e', 'c', 'x','E','C','X','!','*'}
        
    # Check if the message has exactly 5 characters
    if len(message) not in [5, 6]:
        return -1

    # Check if all characters in the message are in allowedChars
    if not all(char in allowedChars for char in message):
        return -1

    # Calculate points based on each letter's position
    totalPoints = sum(calculatePoints(letter, position+1) for position, letter in enumerate(message))
    print(f"Evaluating message '{message}': {totalPoints} points")
    return totalPoints


@bot.message_handler(func=lambda msg: True)
def handle_message(message: Message):
    text = message.text.strip()

    # Mesajın başında sembol olup olmadığını kontrol et
    if text.startswith("*"):
        # Başında '*' sembolü varsa dünü kaydet
        message_text = text[1:].strip()  # Sembolü kaldırıyoruz
        score = evaluateMessage(message_text)
        date = (datetime.now() - timedelta(days=1)).strftime('%d.%m.%Y')  # Dünkü tarih

    elif text.startswith("!"):
        # Başında '!' sembolü varsa 2 gün önceyi kaydet
        message_text = text[1:].strip()  # Sembolü kaldırıyoruz
        score = evaluateMessage(message_text)
        date = (datetime.now() - timedelta(days=2)).strftime('%d.%m.%Y')  # 2 gün önceki tarih

    else:
        # Sembol yoksa bugünü kaydet
        score = evaluateMessage(text)
        date = datetime.now().strftime('%d.%m.%Y')  # Bugünkü tarih


    if score == -1:
        return

    # Kullanıcı bilgilerini CSV'den oku ve güncelle
    users = readUsersFromCsv('data.csv')
    username = get_username_from_msg(message)

    addMissingDates(users, date)

    user = findUserByName(users, username)

    if user:
        # Kullanıcı mevcutsa tarihi ve skoru kaydet
        user.addDay(date, score)
    else:
        # Kullanıcı yoksa oluştur, ardından tarihi ve skoru kaydet
        existing_dates = {date: 0 for date in sorted([date.strftime('%d.%m.%Y') for date in users[0].days.keys()])}
        createUser(users, username, 0, existing_dates)
        user = findUserByName(users, username)
        if user:
            user.addDay(date, score)

    writeUsers2Csv('data.csv', users)

    # Kullanıcıya geri bildirimde bulun
    if text.startswith("!"):
        bot.reply_to(message, f"2 Gün öncenin skoru başarıyla kaydedildi! 2 gün önce: {score} puan kazandınız.")
    elif text.startswith("*"):
        bot.reply_to(message, f"Dünün skoru başarıyla kaydedildi! Dün: {score} puan kazandınız.")
    else:
        bot.reply_to(message, f"Bugünün skoru başarıyla kaydedildi! Bugün: {score} puan kazandınız.")
    if score==36:
        username = get_username_from_msg(message)
        bot.reply_to(message, f"Tebrikler, {username}!Kaydettiğin günde Tüm namazlarını cemaatle kıldın, seni kutluyorum!")


if __name__ == "__main__":
    bot.remove_webhook()  # Ensure no webhook is set
    bot.infinity_polling()  # Start polling