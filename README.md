# Практическая работа №4 — Python, Go, gRPC и mTLS

Автор: Савельев Антон Алексеевич, ЭФБО-12-24.

Django-клиент запрашивает независимые броски кубика напрямую у Go-сервера и через nginx. Снаружи nginx и Go требуют клиентский сертификат. nginx передаёт запрос Go по h2c на loopback внутри той же Linux-среды.

## Быстрый запуск в Docker на macOS или Linux

На этом компьютере используется отдельный профиль Colima `pr4`, поскольку существующий Docker Desktop не запускается. Скрипт `lab.sh` выбирает доступный контекст `colima-pr4`, иначе использует текущий Docker-контекст.

При необходимости запустить Linux-машину: `colima start pr4 --activate=false`.

```sh
sh lab.sh up --build -d
```

Открыть http://127.0.0.1:18000 и http://127.0.0.1:18001, нажать **Roll it!**. Оба клиента работают одновременно с одним Go-сервисом и nginx. Образ основан на Ubuntu 24.04. В контейнере используется Python virtualenv `/opt/venv`; установленные версии сохраняются в `artifacts/python-lock.txt`.

Страница `/checks` показывает сохранённый фактический вывод проверок; обновить её данные можно командой `sh lab.sh exec lab python scripts/collect_evidence.py`.

```sh
sh lab.sh ps
sh lab.sh exec lab python manage.py check
sh lab.sh exec lab go test ./...
sh lab.sh exec lab python manage.py test client -v 2
sh lab.sh exec lab python scripts/integration_test.py
```

## Запуск непосредственно на Ubuntu 24.04

```sh
sh scripts/setup_ubuntu.sh
. venv/bin/activate
python scripts/start.py
```

В отдельном терминале, из корня проекта с активированным окружением:

```sh
python scripts/integration_test.py
```

Для ручного запуска вместо `start.py` нужны четыре терминала:

```sh
./bin/dice-server
nginx -p "$PWD/" -c nginx.conf -g 'daemon off;'
python manage.py runserver 127.0.0.1:8000 --noreload
python manage.py runserver 127.0.0.1:8001 --noreload
```

## Состав проекта

- `proto/api.proto` — контракт сервиса DiceService.
- `client/api/` — сгенерированные Python-stubs и клиент mTLS.
- `client/` и `templates/` — Django и страница с двумя кубиками.
- `server/` — Go-сервер, protobuf-код и тесты.
- `certs/` — настройки CFSSL; `certs.sh` генерирует CA и сертификаты.
- `nginx.conf` — mTLS-прокси и `/nginx_status`.
- `scripts/` — генерация кода, запуск и интеграционные проверки.
- `artifacts/` — журналы и результаты проверок.
- `reports/screenshots/` — фактические скриншоты выполнения; отчёт Word находится в корне проекта.

## Порты

| Назначение | Адрес |
|---|---|
| Django-клиент 1 | http://127.0.0.1:18000 (Ubuntu напрямую: 8000) |
| Django-клиент 2 | http://127.0.0.1:18001 (Ubuntu напрямую: 8001) |
| Прямой gRPC с mTLS | 127.0.0.1:8443 внутри контейнера |
| nginx с mTLS | 127.0.0.1:9448 внутри контейнера |
| Go h2c для nginx | 127.0.0.1:50051 внутри контейнера |

Пути `/grpc` и `/nginx` на каждом Django-клиенте возвращают JSON с результатом соответствующего маршрута. `/health` проверяет доступность Django; полную связность проверяет интеграционный тест.

## Сертификаты

Приватные ключи, PEM-сертификаты и окружение исключены из Git. Создать сертификаты заново:

```sh
sh lab.sh stop
sh lab.sh run --rm lab sh certs.sh
sh lab.sh up -d
```

CA нигде не устанавливается в доверенные хранилища ОС. Публикуются только локальные HTTP-порты 18000 и 18001 (в контейнере 8000 и 8001); это учебный стенд, Django runserver не предназначен для внешнего размещения.

## Остановка

```sh
sh lab.sh down
```

Для остановки отдельной виртуальной машины после работы: `colima stop pr4`.

При запуске непосредственно в Linux остановить `scripts/start.py` через Ctrl+C. Для проверки nginx перед ручным запуском: `nginx -t -p "$PWD/" -c nginx.conf`.

## Исправления относительно методички

Единый порт nginx 9448; корректный модуль и пути генерации Go; относительный импорт Python-stub; шаблон хранится в проекте, а не в site-packages; маршруты `/grpc` и `/nginx` вызывают свои обработчики; номера портов Django передаются позиционным аргументом. Go использует безопасный для параллельных вызовов генератор `crypto/rand`; RPC ограничены таймаутом, процессы завершаются по сигналам.

## Документация

- [gRPC Python](https://grpc.io/docs/languages/python/quickstart/)
- [nginx gRPC](https://nginx.org/en/docs/http/ngx_http_grpc_module.html)
- [Django runserver](https://docs.djangoproject.com/en/5.2/ref/django-admin/#runserver)
