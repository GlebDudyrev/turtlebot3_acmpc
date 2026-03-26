#!/bin/bash
# =============================================================================
# Entrypoint for TurtleBot3 AC-MPC Docker container
# =============================================================================
# Этот скрипт запускает все необходимые сервисы для симуляции TurtleBot3:
# - roscore (ROS master)
# - gzserver (Gazebo симулятор)
# - ros_ign_bridge (мост между Gazebo и ROS2)
# - rosbridge_server (WebSocket для связи с Python на хосте)
# - gzweb (web-интерфейс для просмотра симуляции)
# =============================================================================

set -e  # Остановить скрипт при любой ошибке

# =============================================================================
# Настройка цветного вывода
# =============================================================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# =============================================================================
# Обработка аргументов командной строки
# =============================================================================
# Аргументы:
#   --world NAME  - имя мира (переопределяет WORLD_NAME)
#   --gui         - включить web-интерфейс gzweb
# =============================================================================

GUI_ENABLED="${ENABLE_GUI:-true}"
WORLD_NAME="${WORLD_NAME:-turtlebot3_empty}"

# Разбор аргументов
while [[ $# -gt 0 ]]; do
    case $1 in
        --world)
            WORLD_NAME="$2"
            shift 2
            ;;
        --gui)
            GUI_ENABLED="true"
            shift
            ;;
        *)
            log_warn "Unknown argument: $1"
            shift
            ;;
    esac
done

log_info "Starting TurtleBot3 AC-MPC environment"
log_info "World: ${WORLD_NAME}"
log_info "Model: ${TURTLEBOT3_MODEL:-burger}"
log_info "GUI: ${GUI_ENABLED}"

# =============================================================================
# Определение пути к файлу мира
# =============================================================================
# Сначала ищем в подключенной директории пользовательских миров,
# затем в стандартном пакете turtlebot3-gazebo
# =============================================================================

find_world() {
    local world_name="$1"
    
    # Путь 1: пользовательские миры (configs/worlds -> /home/ubuntu/worlds)
    if [[ -f "/home/ubuntu/worlds/${world_name}.world" ]]; then
        echo "/home/ubuntu/worlds/${world_name}.world"
        return 0
    fi
    
    # Путь 2: стандартные миры turtlebot3-gazebo
    if [[ -f "/opt/ros/humble/share/turtlebot3_gazebo/worlds/${world_name}.world" ]]; then
        echo "/opt/ros/humble/share/turtlebot3_gazebo/worlds/${world_name}.world"
        return 0
    fi
    
    # Путь 3: пробуем просто имя с расширением
    if [[ -f "${world_name}" ]]; then
        echo "${world_name}"
        return 0
    fi
    
    return 1
}

# Найти путь к миру
WORLD_PATH=$(find_world "${WORLD_NAME}") || {
    log_error "World not found: ${WORLD_NAME}"
    exit 1
}

log_info "World path: ${WORLD_PATH}"

# =============================================================================
# Установка переменных окружения ROS
# =============================================================================
# Загрузка ROS2 environment
# =============================================================================
export PATH=/opt/ros/humble/bin:$PATH
source /opt/ros/humble/setup.bash

# Установка модели TurtleBot3
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
log_info "TURTLEBOT3_MODEL=${TURTLEBOT3_MODEL}"

# =============================================================================
# Запуск Gazebo сервера
# =============================================================================
log_info "Starting gzserver with world: ${WORLD_PATH}"
gzserver "${WORLD_PATH}" --verbose -s libgazebo_ros_factory.so &
GZSERVER_PID=$!
sleep 3  # Дать время на запуск симуляции

# =============================================================================
# Генерация робота в мире
# =============================================================================
log_info "Spawning TurtleBot3 model: ${TURTLEBOT3_MODEL}"
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"
ros2 launch turtlebot3_gazebo spawn_turtlebot3.launch.py &
sleep 3

# =============================================================================
# Запуск ros_ign_bridge (мост Gazebo <-> ROS2)
# =============================================================================
# Топики для трансляции:
#   - /scan (LaserScan) - данные лидара
#   - /odom (Odometry)  - одометрия робота
#   - /cmd_vel (Twist) - управление скоростью
# =============================================================================
log_info "Starting ros_ign_bridge..."

# Мост для /scan (лазерный сканер)
ros2 run ros_ign_bridge parameter_bridge /scan@sensor_msgs/msg/LaserScan[ignition.msgs LaserScan &
# Мост для /odom (одометрия)
ros2 run ros_ign_bridge parameter_bridge /odom@nav_msgs/msg/Odometry[ignition.msgs Odometry &
# Мост для /cmd_vel (управление)
ros2 run ros_ign_bridge parameter_bridge /cmd_vel@geometry_msgs/msg/Twist[ignition.msgs Twist &

sleep 2

# =============================================================================
# Запуск rosbridge_server (WebSocket интерфейс)
# =============================================================================
# Порт 9090 - стандартный порт rosbridge
# Позволяет Python коду на хосте подключаться без установки ROS2
# =============================================================================
log_info "Starting rosbridge_server on port 9090..."
ros2 run rosbridge_server rosbridge_websocket.py &
ROSBRIDGE_PID=$!
sleep 2

# =============================================================================
# Запуск gzweb (web-интерфейс Gazebo)
# =============================================================================
# Опционально - для просмотра симуляции в браузере
# Порт 6080
# =============================================================================
if [[ "${GUI_ENABLED}" == "true" ]]; then
    log_info "Starting gzweb on port 6080..."
    gzweb --port=6080 &
    GZWEB_PID=$!
    sleep 2
fi

# =============================================================================
# Ожидание сигнала завершения
# =============================================================================
log_info "All services started successfully!"
log_info "rosbridge WebSocket: localhost:9090"
if [[ "${GUI_ENABLED}" == "true" ]]; then
    log_info "Gazebo Web UI: http://localhost:6080"
fi
log_info "Press Ctrl+C to stop"

# Обработка сигналов завершения
cleanup() {
    log_info "Shutting down..."
    
    # Остановка всех процессов
    [[ -n "${GZWEB_PID}" ]] && kill ${GZWEB_PID} 2>/dev/null
    [[ -n "${ROSBRIDGE_PID}" ]] && kill ${ROSBRIDGE_PID} 2>/dev/null
    [[ -n "${GZSERVER_PID}" ]] && kill ${GZSERVER_PID} 2>/dev/null
    [[ -n "${ROSCORE_PID}" ]] && kill ${ROSCORE_PID} 2>/dev/null
    
    # Убить оставшиеся процессы группы
    kill -- -$$ 2>/dev/null
    
    log_info "Shutdown complete"
    exit 0
}

# Перехват сигналов SIGTERM и SIGINT
trap cleanup SIGTERM SIGINT

# Бесконечный цикл ожидания
wait
