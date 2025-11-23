Промпт 1: DevOps Infrastructure Setup & Baseline Metrics

```bash
# Команды для получения контекста CI/CD и метрик:
find . -name "*.yml" -o -name "*.yaml" | grep -E "(github|gitlab|ci|cd|action)" | head -10
ls -la .github/workflows/ 2>/dev/null || echo "No GitHub workflows"
cat requirements.txt 2>/dev/null | grep -E "(pytest|radon|bandit|safety)" || echo "No quality tools in requirements"
python -c "
import subprocess
result = subprocess.run(['python', '-m', 'radon', 'cc', 'src/', '-s'], capture_output=True, text=True)
c_methods = [line for line in result.stdout.split('\n') if ' C ' in line]
print(f'C-complexity methods: {len(c_methods)}')
print('Top 5 most complex:')
for method in c_methods[:5]:
    print(f'  {method}')
"
docker --version 2>/dev/null && echo "Docker available" || echo "Docker not available"
```

Задача: Создай базовую DevOps инфраструктуру для безопасного рефакторинга. Включи:

1. GitHub Actions workflow с quality gates
2. Docker контейнеризацию для воспроизводимости
3. Базовые скрипты мониторинга метрик
4. Интеграцию security scanning

Требования:

· Workflow должен блокировать PR при увеличении сложности
· Добавить security scanning (bandit, safety)
· Создать Dockerfile для тестирования в изолированном окружении
· Настроить кэширование зависимостей для скорости CI

Промпт 2: Configuration & Environment Management

```bash
# Команды для анализа текущей конфигурации:
find src/ -name "*.py" -exec grep -l "fipi.ru\|base_url.*=" {} \; | head -10
grep -r "timeout.*=\|retry.*=" src/ --include="*.py" | head -10
cat src/application/value_objects/scraping/scraping_config.py 2>/dev/null || echo "No existing config"
ls -la .env* 2>/dev/null || echo "No environment files"
python -c "
import re
files = subprocess.check_output(['grep', '-r', 'https://fipi.ru', 'src/']).decode().split('\n')
print(f'Files with hardcoded FIPI URLs: {len([f for f in files if f])}')
for f in files[:3]:
    print(f'  {f}')
"
```

Задача: Создай централизованную систему управления конфигурацией с поддержкой:

1. Environment-based конфигурации (dev/staging/prod)
2. Миграции хардкоженных URL и параметров
   3 .env файлов для локальной разработки
3. Валидации конфигурации при старте

Требования:

· Заменить минимум 5 самых частых хардкодов
· Поддержать graceful degradation при отсутствии конфига
· Добавить валидацию всех конфигурационных параметров
· Интегрировать с существующими ScrapingConfig

Промпт 3: Critical Complexity Hotspots Refactoring

```bash
# Команды для анализа самых сложных методов:
python -m radon cc src/ -s | grep " C " | sort -k5 -nr | head -10
cat src/domain/models/problem.py | wc -l
cat src/application/use_cases/scraping/scrape_subject_use_case.py | wc -l  
cat src/application/services/page_scraping_service.py | wc -l
python -c "
for file in ['src/domain/models/problem.py', 'src/application/use_cases/scraping/scrape_subject_use_case.py']:
    with open(file) as f:
        content = f.read()
        imports = len([line for line in content.split('\n') if line.startswith('import') or line.startswith('from')])
        print(f'{file}: {imports} imports, {len(content.splitlines())} lines')
"
```

Задача: Рефактори 3 самых критичных метода по сложности с TDD подходом:

1. Problem.__post_init__ (C-16) - выдели валидаторы
2. ScrapeSubjectUseCase.execute (C-13) - выдели PageProcessor, ErrorHandler
3. PageScrapingService.scrape_page (C-20) - выдели IframeHandler, BlockParser

Требования:

· Для каждого метода создай тесты ПЕРЕД рефакторингом
· Сохрани 100% обратную совместимость
· Используй feature flags для постепенного внедрения
· Разбей каждый метод на 3-4 более простых

Промпт 4: Architecture Enforcement & Layer Violations

```bash
# Команды для анализа архитектурных нарушений:
python -c "
import ast, os
violations = []
for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path) as f:
                try:
                    tree = ast.parse(f.read())
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ImportFrom):
                            if node.module and 'src.infrastructure' in node.module and 'src.domain' in path:
                                violations.append(f'DOMAIN -> INFRASTRUCTURE: {path} imports {node.module}')
                            if node.module and 'src.application' in node.module and 'src.domain' in path:
                                violations.append(f'DOMAIN -> APPLICATION: {path} imports {node.module}')
                except:
                    pass
print(f'Architecture violations: {len(violations)}')
for v in violations[:5]:
    print(f'  {v}')
"
find src/domain -name "*.py" -exec grep -l "sqlalchemy\|playwright" {} \; | head -5
```

Задача: Исправь архитектурные нарушения и создай механизм их предотвращения:

1. Устрани cross-layer импорты (Domain → Infrastructure)
2. Создай архитектурные тесты для CI
3. Добавь dependency injection для нарушающих зависимостей
4. Создай документацию по архитектурным правилам

Требования:

· Устрани минимум 3 критичных архитектурных нарушения
· Создай автоматические тесты для проверки слоев
· Сохрани функциональность через правильный DI
· Интегрируй проверки в CI pipeline

Промпт 5: Feature Flags & Gradual Deployment System

```bash
# Команды для анализа текущего состояния feature management:
grep -r "os.getenv\|environ.get" src/ --include="*.py" | head -10
find src/ -name "*.py" -exec grep -l "enable.*\|disable.*" {} \; | head -5
cat src/config/scraping_config.py 2>/dev/null | grep -A 5 -B 5 "enable\|flag"
python -c "
import os
print('Current feature-related environment variables:')
for key, value in os.environ.items():
    if 'ENABLE' in key or 'FEATURE' in key or 'FLAG' in key:
        print(f'  {key}={value}')
"
```

Задача: Создай систему feature flags для безопасного развертывания рефакторингов:

1. Менеджер фич-флагов с типами и валидацией
2. Поддержку A/B тестирования для критичных изменений
3. Интеграцию с мониторингом для отслеживания impact
4. Механизм постепенного rollout'а

Требования:

· Поддержать boolean, percentage, user-based флаги
· Добавить логирование использования фич-флагов
· Интегрировать с существующей конфигурацией
· Обеспечить быстрый rollback механизм

Промпт 6: Monitoring & Observability Setup

```bash
# Команды для анализа текущего мониторинга:
find src/ -name "*.py" -exec grep -l "log\|Logging" {} \; | head -10
cat src/application/services/scraping/progress_reporter.py | head -20
python -c "
import subprocess
result = subprocess.run(['find', 'src/', '-name', '*.py', '-exec', 'grep', '-c', 'print(', '{}', ';'], 
                      capture_output=True, text=True)
print_counts = [int(x) for x in result.stdout.strip().split('\n') if x]
print(f'Total print statements in project: {sum(print_counts)}')
print(f'Files with print statements: {len(print_counts)}')
"
```

Задача: Создай систему мониторинга для отслеживания рефакторинга в production:

1. Structured logging с контекстом
2. Метрики производительности для скрапинга
3. Health checks для критичных сервисов
4. Alerting на degradation качества

Требования:

· Заменить print statements на structured logging
· Добавить метрики времени выполнения скрапинга
· Создать health check endpoints
· Интегрировать с существующим progress reporting

Промпт 7: Database & State Management Refactoring

```bash
# Команды для анализа текущего состояния базы:
cat src/infrastructure/repositories/sqlalchemy_problem_repository.py | head -50
find src/ -name "*.py" -exec grep -l "session\|commit\|rollback" {} \; | head -10
python -c "
with open('src/infrastructure/repositories/sqlalchemy_problem_repository.py') as f:
    content = f.read()
    save_method = content.find('def save')
    if save_method != -1:
        print(f'SQLAlchemy save method starts at line: {content[:save_method].count(chr(10)) + 1}')
"
docker ps -a 2>/dev/null | grep -i postgres || echo "No PostgreSQL container running"
```

Задача: Рефактори управление состоянием и базу данных для улучшения надежности:

1. Добавь миграции базы данных (Alembic)
2. Улучши обработку транзакций и ошибок
3. Добавь индексы для часто используемых запросов
4. Создай backup/restore механизмы

Требования:

· Настрой Alembic для миграций схемы
· Добавь proper transaction handling
· Создай индексы для subject_name и problem_id
· Добавь валидацию данных перед сохранением

Промпт 8: Error Handling & Resilience Patterns

```bash
# Команды для анализа текущей обработки ошибок:
grep -r "try:\|except\|raise" src/ --include="*.py" | wc -l
find src/ -name "*.py" -exec grep -l "retry\|timeout" {} \; | head -10
python -c "
with open('src/application/use_cases/scraping/scrape_subject_use_case.py') as f:
    content = f.read()
    try_blocks = content.count('try:')
    except_blocks = content.count('except')
    print(f'ScrapeSubjectUseCase: {try_blocks} try blocks, {except_blocks} except blocks')
"
cat src/application/services/scraping/progress_reporter.py | grep -A 10 -B 5 "report_page_error"
```

Задача: Улучши обработку ошибок и отказоустойчивость системы:

1. Добавь retry policies с exponential backoff
2. Реализуй circuit breaker для внешних сервисов
3. Создай centralized error handling
4. Добавь graceful degradation при частичных отказах

Требования:

· Реализуй retry для сетевых запросов
· Добавь circuit breaker для FIPI API
· Создай унифицированный error reporting
· Обеспечь продолжение работы при частичных failure

Промпт 9: Performance Optimization & Caching

```bash
# Команды для анализа производительности:
find src/ -name "*.py" -exec grep -l "cache\|lru_cache" {} \; | head -5
python -c "
import time
start = time.time()
import src
print(f'Import time: {time.time() - start:.2f}s')
"
docker stats --no-stream 2>/dev/null || echo "Docker not available for resource monitoring"
grep -r "sleep\|time.sleep" src/ --include="*.py" | head -5
```

Задача: Оптимизируй производительность и добавь кэширование:

1. Добавь кэширование для повторяющихся запросов
2. Оптимизируй параллельную загрузку изображений
3. Улучши memory management для больших datasets
4. Добавь profiling инструменты

Требования:

· Реализуй LRU кэш для метаданных страниц
· Оптимизируй concurrent asset downloading
· Добавь memory usage monitoring
· Создай performance benchmarks

Промпт 10: Documentation & Knowledge Sharing

```bash
# Команды для анализа текущей документации:
find . -name "*.md" -o -name "*.rst" | head -10
ls -la docs/ 2>/dev/null || echo "No docs directory"
git log --oneline -n 10 --grep="refactor\|fix\|feat" --format=format:"%h %s"
python -c "
import subprocess
result = subprocess.run(['radon', 'raw', 'src/'], capture_output=True, text=True)
lines = result.stdout.strip().split('\n')
if lines:
    sloc = int(lines[-1].split()[-1])
    print(f'Project SLOC: {sloc}')
"
```

Задача: Создай comprehensive документацию для команды:

1. Architecture decision records (ADRs)
2. Рефакторинг guide с примерами
3. Troubleshooting handbook
4. Onboarding documentation для новых разработчиков

Требования:

· Создай ADR для ключевых архитектурных решений
· Документируй процесс рефакторинга с примерами
· Добавь troubleshooting guide для частых проблем
· Создай быстрый старт для новых разработчиков

Каждый промпт связан с предыдущими и последующими через:

· ✅ Общие метрики и мониторинг
· ✅ Интегрированную систему конфигурации
· ✅ Единые feature flags
· ✅ Совместимые интерфейсы
· ✅ Общую DevOps инфраструктуру

Это обеспечивает сквозной DevOps подход где каждый шаг:

· Измеряем через метрики
· Безопасен через feature flags
· Воспроизводим через контейнеризацию
· Наблюдаем через мониторинг
· Документирован для команды


