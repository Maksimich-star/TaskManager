import customtkinter as ctk
import tkinter as tk
from datetime import datetime

# Импортируем нашу базу данных
from database import get_session, Task

# Настраиваем внешний вид
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

# Создаём главное окно
app = ctk.CTk()
app.title("Study Planner")
app.geometry("800x700")

# === ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ ===
listbox_to_task_index = []  # Соответствие между Listbox и tasks индексами


# === ФУНКЦИИ ДЛЯ РАБОТЫ С ЗАДАЧАМИ ===


def save_tasks():
    """Сохраняет задачи в базу данных (теперь автоматически)"""
    print("Данные автоматически сохраняются в БД!")


def add_task():
    """Добавляет новую задачу в базу данных"""
    task_text = task_entry.get().strip()
    if task_text:
        session = get_session()
        try:
            new_task = Task(
                text=task_text,
                completed=False
            )
            session.add(new_task)
            session.commit()

            task_entry.delete(0, 'end')
            update_tasks_display()
            update_stats()
            print(f"Добавлена задача: {task_text}")
        except Exception as e:
            session.rollback()
            print(f"Ошибка добавления задачи: {e}")
        finally:
            session.close()


def delete_task():
    """Удаляет выбранную задачу из базы данных"""
    selected_index = tasks_listbox.curselection()
    if selected_index:
        listbox_index = selected_index[0]
        if listbox_index >= 2 and (listbox_index - 2) < len(listbox_to_task_index):
            session = get_session()
            try:
                # Получаем ID задачи из базы данных
                task_id = listbox_to_task_index[listbox_index - 2]
                task = session.query(Task).filter(Task.id == task_id).first()

                if task:
                    session.delete(task)
                    session.commit()
                    update_tasks_display()
                    update_stats()
                    print(f"Удалена задача: {task.text}")
            except Exception as e:
                session.rollback()
                print(f"Ошибка удаления задачи: {e}")
            finally:
                session.close()
        else:
            print("Выберите задачу, а не заголовок")


def toggle_complete():
    """Отмечает задачу как выполненную/невыполненную в базе данных"""
    selected_index = tasks_listbox.curselection()
    if selected_index:
        listbox_index = selected_index[0]
        if listbox_index >= 2 and (listbox_index - 2) < len(listbox_to_task_index):
            session = get_session()
            try:
                task_id = listbox_to_task_index[listbox_index - 2]
                task = session.query(Task).filter(Task.id == task_id).first()

                if task:
                    task.completed = not task.completed
                    session.commit()
                    update_tasks_display()
                    update_stats()
                    status = "выполнена" if task.completed else "не выполнена"
                    print(f"Задача '{task.text}' отмечена как {status}")
            except Exception as e:
                session.rollback()
                print(f"Ошибка изменения статуса: {e}")
            finally:
                session.close()
        else:
            print("Выберите задачу, а не заголовок")


def update_tasks_display():
    """Обновляет список задач в виде таблицы с цветами"""
    tasks_listbox.delete(0, 'end')
    today = datetime.now().date()

    # Получаем задачи из базы данных
    session = get_session()
    try:
        tasks = session.query(Task).all()

        # Временный список для сортировки (сохраняем ID задач)
        sorted_tasks = []

        for task in tasks:
            # Определяем приоритет для сортировки
            priority = 0
            days_left = None
            if task.deadline and not task.completed:
                try:
                    deadline_date = datetime.strptime(task.deadline, "%Y-%m-%d").date()
                    days_left = (deadline_date - today).days

                    if days_left < 0:
                        priority = 0
                    elif days_left == 0:
                        priority = 1
                    elif days_left <= 3:
                        priority = 2
                    else:
                        priority = 3
                except ValueError:
                    priority = 4
                    days_left = None
            else:
                priority = 4

            # Сохраняем ID задачи вместо индекса
            sorted_tasks.append((priority, days_left, task.id, task))

        # Сортируем по приоритету
        sorted_tasks.sort(key=lambda x: x[0])

        # Добавляем заголовок таблицы с правильным выравниванием
        status_header = "Статус".center(8)  # 8 символов для статуса
        task_header = "Задача".ljust(35)  # 35 символов для задачи
        deadline_header = "Срок выполнения".ljust(20)  # 20 символов для срока

        header = f"{status_header} | {task_header} | {deadline_header}"
        tasks_listbox.insert('end', header)
        tasks_listbox.itemconfig('end', fg='#888888')

        # Добавляем разделитель
        separator = "―" * 70  # Немного короче для лучшего вида
        tasks_listbox.insert('end', separator)
        tasks_listbox.itemconfig('end', fg='#444444')

        # Сохраняем соответствие между позицией в Listbox и ID задачи
        global listbox_to_task_index
        listbox_to_task_index = []

        # Добавляем задачи в таблицу
        for priority, days_left, task_id, task in sorted_tasks:
            status = "✓" if task.completed else "☐"

            # Форматируем информацию о сроке
            deadline_text = ""
            text_color = "white"  # по умолчанию

            if task.deadline and not task.completed and days_left is not None:
                if days_left < 0:
                    text_color = "red"
                    deadline_text = f"{abs(days_left)} дн. просрочено"
                elif days_left == 0:
                    text_color = "yellow"
                    deadline_text = "сегодня"
                elif days_left <= 3:
                    text_color = "orange"
                    deadline_text = f"{days_left} дн."
                else:
                    deadline_text = f"{days_left} дн."
            elif task.completed:
                deadline_text = "выполнено"
            else:
                deadline_text = "нет срока"

            # ОГРАНИЧИВАЕМ длину текста задачи
            max_task_length = 35
            display_task_text = task.text
            if len(display_task_text) > max_task_length:
                display_task_text = display_task_text[:max_task_length - 3] + "..."

            # Создаем строку таблицы с ВЫРАВНИВАНИЕМ
            status_col = f"{status:^8}"  # Центрируем статус (8 символов)
            task_col = f"{display_task_text:35}"  # Задача слева (35 символов)
            deadline_col = f"{deadline_text:20}"  # Срок слева (20 символов)

            display_text = f"{status_col} | {task_col} | {deadline_col}"

            # Добавляем в список
            tasks_listbox.insert('end', display_text)

            # Сохраняем соответствие: позиция в Listbox -> ID задачи
            listbox_to_task_index.append(task_id)

            # Устанавливаем цвет для ВСЕЙ строки
            if text_color == "red":
                tasks_listbox.itemconfig('end', fg='#ff6666')
            elif text_color == "yellow":
                tasks_listbox.itemconfig('end', fg='#ffff99')
            elif text_color == "orange":
                tasks_listbox.itemconfig('end', fg='#ffaa66')
            elif task.completed:
                tasks_listbox.itemconfig('end', fg='#88ff88')  # Зеленый для выполненных

    except Exception as e:
        print(f"Ошибка обновления отображения: {e}")
    finally:
        session.close()


def update_stats():
    """Обновляет статистику"""
    session = get_session()
    try:
        total = session.query(Task).count()
        completed = session.query(Task).filter(Task.completed == True).count()
        progress_text = f"Всего задач: {total} | Выполнено: {completed} | Не выполнено: {total - completed}"

        stats_label.configure(text=progress_text)

        progress = completed / total * 100 if total > 0 else 0
        print(f"Прогресс: {progress:.1f}%")
        print(f"Статистика в приложении: {progress_text}")
    finally:
        session.close()


def on_closing():
    """Функция при закрытии окна"""
    save_tasks()
    app.destroy()


def add_task_with_deadline():
    """Добавляет задачу с дедлайном через диалоговое окно"""
    task_text = task_entry.get().strip()
    if not task_text:
        return

    # Создаём диалоговое окно для выбора даты
    dialog = ctk.CTkInputDialog(
        text="Введите дедлайн (дд.мм.гггг) или оставьте пустым:",
        title="Дедлайн задачи"
    )
    deadline_text = dialog.get_input()

    # Обрабатываем введённую дату
    deadline = None
    if deadline_text:
        try:
            deadline = datetime.strptime(deadline_text, "%d.%m.%Y").strftime("%Y-%m-%d")
        except ValueError:
            print("Неверный формат даты, задача без дедлайна")

    session = get_session()
    try:
        new_task = Task(
            text=task_text,
            completed=False,
            deadline=deadline
        )
        session.add(new_task)
        session.commit()

        task_entry.delete(0, 'end')
        update_tasks_display()
        update_stats()
        check_deadlines()
        print(f"Добавлена задача: {task_text} с дедлайном: {deadline}")
    except Exception as e:
        session.rollback()
        print(f"Ошибка добавления задачи: {e}")
    finally:
        session.close()


def check_deadlines():
    """Проверяет приближающиеся дедлайны"""
    today = datetime.now().date()
    upcoming_deadlines = []

    session = get_session()
    try:
        tasks = session.query(Task).filter(Task.deadline.isnot(None), Task.completed == False).all()

        for task in tasks:
            try:
                deadline_date = datetime.strptime(task.deadline, "%Y-%m-%d").date()
                days_left = (deadline_date - today).days

                if 0 <= days_left <= 3:
                    upcoming_deadlines.append(f"'{task.text}' - {days_left} дн.")
            except ValueError:
                continue

        if upcoming_deadlines:
            warning_text = "⚠️ Срочные задачи:\n" + "\n".join(upcoming_deadlines)
            print(warning_text)
    finally:
        session.close()


def show_full_task():
    """Показывает полный текст выбранной задачи"""
    selected_index = tasks_listbox.curselection()
    if selected_index:
        listbox_index = selected_index[0]
        # Пропускаем заголовок и разделитель (первые 2 строки)
        if listbox_index >= 2 and (listbox_index - 2) < len(listbox_to_task_index):
            task_id = listbox_to_task_index[listbox_index - 2]

            session = get_session()
            try:
                task = session.query(Task).filter(Task.id == task_id).first()
                if not task:
                    print("Задача не найдена")
                    return

                # Создаем окно с полным текстом
                dialog = ctk.CTkToplevel(app)
                dialog.title("Полный текст задачи")
                dialog.geometry("500x350")
                dialog.transient(app)
                dialog.grab_set()

                # Заголовок
                title_label = ctk.CTkLabel(dialog, text="Полный текст задачи:", font=("Arial", 16, "bold"))
                title_label.pack(pady=10)

                # Текст задачи
                task_text = ctk.CTkTextbox(dialog, width=450, height=200, font=("Arial", 12))
                task_text.pack(pady=10, padx=20)
                task_text.insert("1.0", task.text)
                task_text.configure(state="disabled")

                # Кнопка закрытия
                close_btn = ctk.CTkButton(dialog, text="Закрыть", command=dialog.destroy)
                close_btn.pack(pady=10)

            except Exception as e:
                print(f"Ошибка показа задачи: {e}")
            finally:
                session.close()


# === СОЗДАЁМ ЭЛЕМЕНТЫ ИНТЕРФЕЙСА ===

# Заголовок
title_label = ctk.CTkLabel(
    app,
    text="⭐ Мой учебный планировщик",
    font=("Arial", 20, "bold")
)
title_label.pack(pady=20)

# Поле для ввода
task_entry = ctk.CTkEntry(
    app,
    placeholder_text="Введите новую учебную задачу...",
    width=400,
    height=40
)
task_entry.pack(pady=10)

# Привязываем Enter к добавлению задачи
task_entry.bind('<Return>', lambda event: add_task_with_deadline())

# Кнопка добавления
add_button = ctk.CTkButton(
    app,
    text="Добавить задачу",
    width=150,
    height=40,
    command=add_task_with_deadline  # Привязываем функцию
)
add_button.pack(pady=10)

# Фрейм для кнопок
button_frame = ctk.CTkFrame(app)
button_frame.pack(pady=10)

# Кнопки управления
delete_button = ctk.CTkButton(
    button_frame,
    text="Удалить",
    width=120,
    height=35,
    fg_color="#d9534f",
    command=delete_task  # Привязываем функцию
)
delete_button.pack(side="left", padx=5)

complete_button = ctk.CTkButton(
    button_frame,
    text="Отметить выполнено",
    width=120,
    height=35,
    fg_color="#5cb85c",
    command=toggle_complete  # Привязываем функцию
)
complete_button.pack(side="left", padx=5)

# ДОБАВЬТЕ ЭТУ КНОПКУ - Просмотреть полный текст
view_button = ctk.CTkButton(
    button_frame,
    text="Просмотреть",
    width=120,
    height=35,
    fg_color="#337ab7",
    command=show_full_task
)
view_button.pack(side="left", padx=5)

# Список задач (заменяем Label на Listbox)
tasks_listbox = tk.Listbox(
    app,
    width=70,
    height=20,
    font=("Courier New", 11),  # Моноширинный шрифт для ровных столбцов
    bg="#2b2b2b",
    fg="white",
    selectbackground="#3b8ed0"
)
tasks_listbox.pack(pady=20)

tasks_listbox.bind('<Double-Button-1>', lambda event: show_full_task())

# Статистика - создаём отдельный фрейм для лучшего отображения
stats_frame = ctk.CTkFrame(app)
stats_frame.pack(side="bottom", fill="x", pady=10)

stats_label = ctk.CTkLabel(
    stats_frame,
    text="Всего задач: 0 | Выполнено: 0 | Не выполнено: 0",
    font=("Arial", 14, "bold")

)
stats_label.pack(pady=10)

# === ЗАПУСК ПРИЛОЖЕНИЯ ===

# Загружаем задачи при старте
update_tasks_display()  # Вместо load_tasks()

# Сохраняем при закрытии окна
app.protocol("WM_DELETE_WINDOW", on_closing)

# Запускаем приложение
app.mainloop()
