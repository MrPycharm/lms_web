import time
from PyQt5.QtGui import QImage
from telegram import ReplyKeyboardMarkup
from telegram.ext import Application, MessageHandler, filters, ConversationHandler
from telegram.ext import CommandHandler
import sqlite3
import sys
from PyQt5.QtWidgets import QMainWindow, QApplication
from PyQt5.QtGui import QPainter, QColor, QFont
from PyQt5.QtCore import Qt

reply_keyboard = [['/add', '/delete', '/roles', '/stop'],
                  ['/run']]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=False)

async def help(update, context):
    await update.message.reply_text("Привет! Я бот альманах.")
    time.sleep(1)
    await update.message.reply_text(
        "Я помогаю запоминать даты и лучше разбираться в истории."
    )
    time.sleep(1)
    await update.message.reply_text("Если кратко, то:\n"
                                    "/add - добавить персонажа/событие в таймлайн\n"
                                    "/delete - удалить персонажа/событие из таймлайна\n"
                                    "/roles - узнать роли\n"
                                    "/run - увидеть таймлайн",
        reply_markup=markup
                                    )


async def delete(update, context):

    await update.message.reply_text(
        "Привет, тут вы можете удалить персонажа или событие. \n"
        "Вы можете прервать ввод, послав команду /stop. \n"
        "Введите имя/название. ")
    return 1

async def roles(update, context):
    conn = sqlite3.connect("HistoryProject.sqlite")
    cur = conn.cursor()
    test = cur.execute(f"""SELECT description FROM roles""").fetchall()
    # print("\n".join([x[0] for x in test]))
    conn.commit()
    conn.close()
    await update.message.reply_text("Роли:")
    time.sleep(1)
    await update.message.reply_text("\n".join([x[0] for x in test]))

async def delete_second_response(update, context):
    # Используем user_data в ответе.
    name = update.message.text
    conn = sqlite3.connect("HistoryProject.sqlite")
    cur = conn.cursor()

    # удаление по имени из object
    test = cur.execute(f"""SELECT * FROM object WHERE name == '{name}' """).fetchall()
    cur.execute(f"""DELETE FROM object WHERE name = '{name}' """)
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"Спасибo! Персонаж/событие {name} удалено!")
    context.user_data.clear()  # очищаем словарь с пользовательскими данными
    return ConversationHandler.END


async def add(update, context):
    await update.message.reply_text(
        "Привет, тут вы можете добавить персонажа или событие.\n"
        "Вы можете прервать ввод, послав команду /stop. \n"
        "Введите имя/название.")
    return 1


async def first_response(update, context):
    # Сохраняем ответ в словаре.
    context.user_data['name'] = update.message.text
    await update.message.reply_text(
        "Введите начальную дату.")
    return 2


async def second_response(update, context):
    # Сохраняем ответ в словаре.
    context.user_data['start'] = update.message.text
    await update.message.reply_text(
        "Введите конечную дату.")
    return 3


async def third_response(update, context):
    # Сохраняем ответ в словаре.
    context.user_data['end'] = update.message.text
    await update.message.reply_text(
        "Введите роль.")
    return 4


# Добавили словарь user_data в параметры.
async def fourth_response(update, context):
    # weather = update.message.text
    context.user_data['role'] = update.message.text
    await update.message.reply_text(
        "Спасибо!")

    # context.user_data = {'name': 'привет', 'start': '1800', 'end': '2000', 'role': 'нет'}

    name, start, end, role = context.user_data['name'], context.user_data['start'], context.user_data['end'], \
        context.user_data['role']
    conn = sqlite3.connect('HistoryProject.sqlite')
    cursor = conn.cursor()
    a = cursor.execute(f"SELECT id FROM roles WHERE '{role}' == description").fetchall()[0][0]
    # достаём из roles id роли
    conn.commit()
    conn.close()

    conn = sqlite3.connect('HistoryProject.sqlite')
    cursor2 = conn.cursor()
    sql = "INSERT INTO object (name, start, end, role_id) VALUES (?, ?, ?, ?)"
    values = (name, start, end, a)
    # добавляем в object
    cursor2.execute(sql, values)
    conn.commit()
    conn.close()

    context.user_data.clear()  # очищаем словарь с пользовательскими данными
    return ConversationHandler.END


async def stop(update, context):
    context.user_data.clear()  # очищаем словарь с пользовательскими данными
    await update.message.reply_text("Всего доброго!")
    return ConversationHandler.END


async def run(update, context):
    app = QApplication(sys.argv)
    main_form = TimelineWindow()
    main_form.saveAsImage()
    await update.message.reply_photo(photo='output6_image.png')
    return


class TimelineWindow(QMainWindow):  # вывод информации (main)
    def __init__(self):
        super().__init__()
        # создание поля (фона)
        self.setWindowTitle("Timeline")
        self.setGeometry(100, 100, 1500, 600)
        self.setStyleSheet("background-color: rgb(217, 217, 211);")
        self.show()

    def paintEvent(self, event):
        qp = QPainter(self)
        qp.setPen(Qt.black)

        conn = sqlite3.connect('HistoryProject.sqlite')
        cursor = conn.cursor()

        # получение названия ролей из roles
        cursor.execute("SELECT description FROM roles")
        roles_data = cursor.fetchall()
        cursor.execute("SELECT name, start, end, role_id FROM object")
        # получение всей информации из object
        objects_data = cursor.fetchall()
        conn.close()

        font = QFont("Arial", 10)
        qp.setFont(font)

        timeline_start = 1800  # timeline start year
        timeline_end = 2023  # timeline end year

        timeline_width = self.width() - 50
        timeline_height = 30
        bar_width = timeline_width / (timeline_end - timeline_start + 1)

        storage = {}  # создание словаря для хранения границ объектов
        for obj in objects_data:
            name, start, end, role_id = obj
            con_r = sqlite3.connect('HistoryProject.sqlite')
            cursor_r = con_r.cursor()
            colour = cursor_r.execute(f"SELECT color FROM roles WHERE id == '{role_id}' ").fetchall()[0][0].split(',')
            role_color = QColor(int(colour[0]), int(colour[1]), int(colour[2]))
            con_r.close()

            # подготовка к рисованию
            x_start = int((start - timeline_start) * bar_width) + 50
            x_end = int((end - timeline_start) * bar_width) + 50

            qp.setBrush(role_color)
            qp.setPen(Qt.white)

            # функция for для получения нужной строчки (так, чтобы информация друг на друга не наслаивалась)
            flag = False
            for key, coords in storage.items():
                if flag:
                    break
                for tupl in coords:
                    if tupl[0] < start < tupl[1] or tupl[0] < end < tupl[1] or start < tupl[0] and end > tupl[1]:
                        # проверка границ
                        break
                else:  # если программа проработала нормально, т.е. ни в одном случае границы не пересекаются, то:
                    qp.drawRect(x_start, key // 2 - 10, x_end - x_start, 20)
                    qp.drawText(x_start, key // 2 - 10, x_end - x_start, 20, Qt.AlignCenter, name)
                    storage[key].append((start, end))
                    # добавление границ в storage
                    flag = True
                    break
            else:
                if storage:
                    # переход на новую строку
                    height = max(storage.keys()) + 45
                    qp.drawRect(x_start, height // 2 - 10, x_end - x_start, 20)
                    qp.drawText(x_start, height // 2 - 10, x_end - x_start, 20, Qt.AlignCenter, name)
                    storage[height] = [(start, end)]
                else:
                    # storage пуст  -  происходит один раз в самом начале
                    qp.drawRect(x_start, timeline_height // 2 - 10, x_end - x_start, 20)
                    qp.drawText(x_start, timeline_height // 2 - 10, x_end - x_start, 20, Qt.AlignCenter, name)
                    storage[timeline_height] = [(start, end)]

    def except_hook(cls, exception, traceback):
        sys.__excepthook__(cls, exception, traceback)

    def saveAsImage(self):
        img = QImage(self.size(), QImage.Format_ARGB32)
        img.fill(Qt.transparent)
        painter = QPainter(img)
        self.render(painter)
        painter.end()

        img.save('output6_image.png')


def main():
    application = Application.builder().token('TOKEN').build()
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('add', add)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, first_response)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, second_response)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, third_response)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, fourth_response)]
        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    del_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('delete', delete)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_second_response)]

        },
        fallbacks=[CommandHandler('stop', stop)]
    )

    application.add_handler(conv_handler)
    application.add_handler(del_conv_handler)
    application.add_handler(CommandHandler("run", run))
    application.add_handler(CommandHandler("roles", roles))
    application.add_handler(CommandHandler(["start", "help"], help))

    # application.add_handler(CommandHandler("run", run))
    application.run_polling()


if __name__ == '__main__':
    main()
