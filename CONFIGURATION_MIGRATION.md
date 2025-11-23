# Миграция на централизованную систему конфигурации

## Обзор

Система была обновлена для использования централизованной конфигурации с поддержкой:

- Environment-based конфигурации (dev/staging/prod)
- .env файлов для локальной разработки  
- Валидации конфигурации при старте
- Graceful degradation при отсутствии конфига

## Замененные хардкоды

1. **Базовые URL**: `https://fipi.ru`, `https://ege.fipi.ru`
2. **Таймауты**: 30 секунд в браузере и скачивании
3. **Повторные попытки**: 3 попытки с задержкой 1 секунда
4. **User Agent**: строка по умолчанию
5. **Директории**: `./assets` для файлов

## Использование

### Для разработки

1. Скопируйте `.env.example` в `.env`
2. Настройте параметры по необходимости
3. Запускайте приложение как обычно

### Для продакшена

1. Создайте `.env.prod` с production настройками
2. Установите `ENVIRONMENT=prod`
3. Убедитесь, что все URL используют HTTPS

### Программное использование

```python
from src.core.config import config

# Получение конфигурационных значений
base_url = config.scraping.base_url
timeout = config.browser.timeout_seconds
assets_dir = config.assets_directory

# Интеграция с существующим ScrapingConfig
from src.application.value_objects.scraping.scraping_config import ScrapingConfig
scraping_config = ScrapingConfig.from_central_config()
```

Graceful Degradation

Если центральная конфигурация недоступна, система использует безопасные значения по умолчанию и продолжает работу с предупреждениями в логах.

Валидация

Конфигурация валидируется при:

· Загрузке приложения
· Изменении environment файлов
· Явном вызове validate_configuration_on_startup()

Ошибки валидации логируются, но не останавливают приложение (graceful degradation).
