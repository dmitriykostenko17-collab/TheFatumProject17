# 🚀 Инструкция для запуска сборки APK

## Шаг 1️⃣: Создать GitHub репозиторий

1. Перейти на https://github.com/new
2. Назвать репозиторий: `VFatumbot_Python`
3. Выбрать **Public** (для Actions)
4. Нажать **Create repository**
5. **Скопировать URL репо** (выглядит как `https://github.com/YOUR_USER/VFatumbot_Python.git`)

## Шаг 2️⃣: Отправить код на GitHub

Открыть PowerShell в папке проекта и выполнить:

```powershell
# Инициализируем git
git init

# Добавляем все файлы
git add .

# Первый коммит
git commit -m "Initial commit: VFatumbot Android Flet app"

# Переименовываем ветку в main (если нужно)
git branch -M main

# Добавляем remote (ВСТАВЬТЕ ВАШ URL)
git remote add origin https://github.com/YOUR_USER/VFatumbot_Python.git

# Загружаем на GitHub
git push -u origin main
```

## Шаг 3️⃣: Запустить сборку автоматически

Проект автоматически запустится при каждом push. Но если хотите сразу:

1. Перейти на GitHub → ваш репо
2. Вкладка **Actions**
3. Слева выбрать **Build Android APK**
4. Нажать **Run workflow** → **Run workflow**

## Шаг 4️⃣: Скачать готовый APK

1. Дождись завершения (будет зеленая галочка ~10-15 мин)
2. Кликнуть на успешный запуск
3. Внизу **Artifacts** → скачать `app-release-apk.zip`
4. Распаковать `.apk` → установить на телефон

---

## 📝 Команды для обновлений

После изменений в коде:

```powershell
git add .
git commit -m "Описание ваших изменений"
git push
```

GitHub автоматически соберет новый APK!

---

## ✅ Проверка статуса

- **Actions tab** → Видите статус сборки
- **Зеленая галочка** ✓ = сборка успешна
- **Красный крест** ✗ = есть ошибка

Если ошибка, кликните на workflow и посмотрите логи.
