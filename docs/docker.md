# Настройка Docker и симуляции TurtleBot3

## Требования

- Docker и Docker Compose
- Ubuntu 22.04 (рекомендуется)
- Gazebo Classic 11 (для визуализации)

---

## Установка Gazebo Classic

Для визуализации симуляции на хосте необходимо установить Gazebo Classic 11:

```bash
# Добавить PPA
sudo add-apt-repository ppa:openrobotics/gazebo11-gz-cli

# Обновить и установить
sudo apt update
sudo apt install gazebo11
```

---

## Сборка и запуск контейнера

### 1. Перейти в директорию проекта

```bash
cd ~/turtlebot3_acmpc/docker
```

### 2. Собрать образ

```bash
docker-compose build
```

### 3. Запустить контейнер

```bash
docker-compose up
```

Контейнер запустит:
- Gazebo сервер (gzserver)
- TurtleBot3 в симуляции
- rosbridge_server на порту 9090

---

## Подключение визуализации

После запуска контейнера, на хосте можно подключить GUI:

```bash
gzclient
```

Это откроет окно Gazebo с визуализацией симуляции из контейнера.

---

## Подключение через Python

Для управления роботом из Python используется rosbridge:

```python
import roslibpy

# Подключение к rosbridge
ros = roslibpy.Ros(host='localhost', port=9090)
ros.run()

# Пример: подписаться на scan
def on_scan(message):
    print('Scan data:', message)

scan_sub = roslibpy.Topic(ros, '/scan', 'sensor_msgs/LaserScan')
scan_sub.subscribe(on_scan)

# Пример: отправить команду движения
cmd_pub = roslibpy.Topic(ros, '/cmd_vel', 'geometry_msgs/Twist')
cmd_pub.publish(roslibpy.Message({
    'linear': {'x': 0.1, 'y': 0.0, 'z': 0.0},
    'angular': {'x': 0.0, 'y': 0.0, 'z': 0.0}
}))
```

---

## Доступные топики

| Топик | Тип | Описание |
|-------|-----|---------|
| /scan | sensor_msgs/LaserScan | Данные лидара |
| /odom | nav_msgs/Odometry | Одометрия робота |
| /cmd_vel | geometry_msgs/Twist | Управление скоростью |
| /tf | tf2_msgs/TFMessage | Transform дерево |

---

## Переменные окружения

При необходимости можно изменить параметры симуляции:

```bash
# Изменить модель робота
export TURTLEBOT3_MODEL=waffle
docker-compose up

# Изменить мир
export WORLD_NAME=my_custom_world
docker-compose up
```

Доступные модели: burger, waffle, waffle_pi

---

## Устранение проблем

### Порт занят

```bash
# Найти процесс
sudo lsof -i :11345

# Убить процесс
sudo kill -9 <PID>
```

### Порт 9090 занят (rosbridge)

```bash
# Найти процесс
sudo lsof -i :9090

# Убить процесс
sudo kill -9 <PID>
```

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs

# Пересобрать
docker-compose build --no-cache
```

### Ошибка "No route to host"

Проблема с сетевым подключением. Попробуйте:

```bash
# Использовать network_mode: bridge в docker-compose.yml
# Раскомментировать ports:
#   - "9090:9090"
#   - "11345:11345"
```

### Gazebo не запускается внутри контейнера

```bash
# Проверить что установлены все зависимости
docker exec -it acmpc_gazebo ros2 pkg list | grep gazebo

# Проверить переменные окружения
docker exec -it acmpc_gazebo env | grep GAZEBO
```

---

## Структура Docker

### docker-compose.yml

```yaml
services:
  acmpc_gazebo:
    build: .
    container_name: acmpc_gazebo
    restart: unless-stopped
    network_mode: host
    environment:
      - ROS_DOMAIN_ID=42
      - TURTLEBOT3_MODEL=burger
      - WORLD_NAME=turtlebot3_dqn_stage2
    volumes:
      - ../configs/worlds:/workspace/worlds:ro
    entrypoint: /entrypoint.sh
```

### Dockerfile

Основан на `ros:humble-ros-base-jammy`, включает:
- Gazebo 11
- ROS 2 Humble
- TurtleBot3 пакеты
- rosbridge_server

### Entrypoint

Скрипт запуска:
1. Устанавливает переменные окружения
2. Запускает Gazebo с TurtleBot3
3. Запускает rosbridge_server

---

## Сетевые настройки

### Host mode (по умолчанию)

Контейнер использует сетевое пространство хоста:
- rosbridge: localhost:9090
- Gazebo Master: localhost:11345

### Bridge mode (альтернатива)

```yaml
network_mode: bridge
ports:
  - "9090:9090"    # rosbridge WebSocket
  - "11345:11345"  # Gazebo Master
```

---

## Кастомизация

### Добавление своего мира

1. Создать файл мира в `configs/worlds/`
2. Установить переменную окружения:
   ```bash
   export WORLD_NAME=my_custom_world
   docker-compose up
   ```

### Использование другой модели робота

```bash
export TURTLEBOT3_MODEL=waffle
docker-compose up
```

Доступные модели: `burger`, `waffle`, `waffle_pi`

### Запуск без пересборки

```bash
docker-compose up --no-build
```
