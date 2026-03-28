# Настройка Docker и симуляции TurtleBot3

## Требования

- Docker
- Ubuntu 22.04
- Gazebo Classic 11

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
ros.connect()

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

### Контейнер не запускается

```bash
# Проверить логи
docker-compose logs

# Пересобрать
docker-compose build --no-cache
```
