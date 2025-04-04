#!/bin/bash

# Включаем строгий режим: выходить при ошибке, при использовании необъявленной переменной,
# и учитывать ошибки в конвейерах (pipes)
set -euo pipefail

# --- Параметры ---
LOCAL_FILE="download.lock"
ZIP_FILE="by-full.zip"
DOWNLOAD_URL="https://tools.by/archives/product-images/by-full.zip"
TARGET_DIR="img_storage"
DAYS_OLD_THRESHOLD=3 # Файл должен быть старше этого количества дней

# --- Вычисляем порог в секундах ---
# Секунд в дне = 24 часа * 60 минут * 60 секунд = 86400
THRESHOLD_SECONDS=$(( DAYS_OLD_THRESHOLD * 86400 ))

echo "--- Начало проверки ---"
echo "Текущее время: $(date)"
echo "Порог возраста: $DAYS_OLD_THRESHOLD дней ($THRESHOLD_SECONDS секунд)"

# --- Логика проверки возраста файла ---
RUN_UPDATE=false # По умолчанию - не обновлять

# Проверяем, существует ли файл
if [ -f "$LOCAL_FILE" ]; then
  echo "Файл '$LOCAL_FILE' найден."

  # Получаем текущее время в Unix timestamp
  current_time=$(date +%s)

  # Получаем время последней модификации файла в Unix timestamp
  # ВАЖНО: Формат stat отличается в Linux и macOS!
  if [[ "$(uname)" == "Linux" ]]; then
    file_mod_time=$(stat -c %Y "$LOCAL_FILE")
  elif [[ "$(uname)" == "Darwin" ]]; then # macOS
    file_mod_time=$(stat -f %m "$LOCAL_FILE")
  else
    echo "Ошибка: Неизвестная ОС для команды stat. Невозможно определить время файла."
    exit 1
  fi

  # Вычисляем возраст файла в секундах
  file_age_seconds=$(( current_time - file_mod_time ))

  echo "Текущее время (unix): $current_time"
  echo "Время файла (unix):  $file_mod_time"
  echo "Возраст файла (сек): $file_age_seconds"

  # Сравниваем возраст с порогом
  if (( file_age_seconds > THRESHOLD_SECONDS )); then
    echo "РЕЗУЛЬТАТ ПРОВЕРКИ: Файл СТАРЫЙ (возраст $file_age_seconds сек > порога $THRESHOLD_SECONDS сек). Требуется обновление."
    RUN_UPDATE=true
  else
    echo "РЕЗУЛЬТАТ ПРОВЕРКИ: Файл СВЕЖИЙ (возраст $file_age_seconds сек <= порога $THRESHOLD_SECONDS сек). Обновление не требуется."
    # RUN_UPDATE остается false
  fi

else
  # Файл не существует. Требуется обновление.
  echo "РЕЗУЛЬТАТ ПРОВЕРКИ: Файл '$LOCAL_FILE' НЕ НАЙДЕН. Требуется обновление."
  RUN_UPDATE=true
fi

# --- Основная часть скрипта ---
if [ "$RUN_UPDATE" = true ]; then
  echo "--- Запуск процесса обновления ---"

  # Пересоздаем локальный файл
  rm -f $LOCAL_FILE
  touch $LOCAL_FILE

  # 0. Удаляем СТАРЫЙ zip-файл, если он был причиной обновления (чтобы wget скачал новый)
  #    Делаем это только если он существует, на случай если обновление было из-за отсутствия файла.
  if [ -f "$ZIP_FILE" ]; then
      echo "Удаляем старый файл '$ZIP_FILE'..."
      rm -f "$ZIP_FILE"
  fi

  # 1. Очистка целевой директории (перед скачиванием/распаковкой)
  echo "Очистка директории '$TARGET_DIR'..."
  # Создаем директорию, если она не существует, и игнорируем ошибку, если существует
  mkdir -p "$TARGET_DIR"
  # Удаляем содержимое, а не саму директорию, чтобы избежать проблем с правами
  rm -rf "${TARGET_DIR:?}/"* # :? защитит от случайного удаления /, если TARGET_DIR пуста

  # 2. Скачиваем новый архив
  echo "Скачивание нового архива '$ZIP_FILE' с $DOWNLOAD_URL..."
  if wget -O "$ZIP_FILE" "$DOWNLOAD_URL"; then
    echo "Архив успешно скачан."
  else
    echo "Ошибка: Не удалось скачать архив с $DOWNLOAD_URL."
    # Можно удалить недокачанный файл, если wget его создает
    rm -f "$ZIP_FILE"
    exit 1 # Выходим с ошибкой
  fi

  # 3. Распаковка
  echo "Распаковка '$ZIP_FILE' в '$TARGET_DIR'..."
  if unzip -q "$ZIP_FILE" -d "$TARGET_DIR"; then # -q для тихого режима
    echo "Архив успешно распакован."
  else
    echo "Ошибка: Не удалось распаковать архив '$ZIP_FILE'."
    # Оставляем zip для анализа ошибки
    exit 1 # Выходим с ошибкой
  fi
  
  # 4. Удаляем zip-архив Незачем его хранить
  echo "Удаление архива '$ZIP_FILE'..."
  rm -f "$ZIP_FILE"

  # 5. Очистка ненужных файлов внутри img_storage
  echo "Поиск и удаление '0.jpg' в '$TARGET_DIR'..."
  find "$TARGET_DIR/" -type f -name "0.jpg" -print -delete
  # find "$TARGET_DIR/" -type f -name "0.jpg" -exec rm -f {} \; # Альтернатива с exec

  echo "Поиск и удаление пустых директорий в '$TARGET_DIR'..."
  # Удаляем снизу вверх, чтобы обработать вложенные пустые директории
  find "$TARGET_DIR/" -depth -type d -empty -print -delete

  echo "--- Процесс обновления завершен успешно ---"

else
  echo "--- Обновление пропущено (файл свежий) ---"
fi

exit 0