# =============================================================================
# TurtleBot3 AC-MPC Docker Environment
# =============================================================================
# Базовый образ: ROS 2 Humble без GUI
# Используем ros-base для уменьшения размера образа
# =============================================================================
FROM ros:humble-ros-base-jammy

# =============================================================================
# Настройка shell для выполнения команд
# =============================================================================
SHELL ["/bin/bash", "-c"]

# =============================================================================
# Установка системных зависимостей
# =============================================================================
RUN apt-get update && apt-get install -y \
    lsb-release \
    wget \
    gnupg \
    curl \
    ca-certificates \
    locales \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Настройка локали
# =============================================================================
RUN locale-gen en_US en_US.UTF-8 && \
    update-locale LANG=en_US.UTF-8
ENV LANG=en_US.UTF-8

# =============================================================================
# Установка ROS-пакетов для Gazebo Fortress
# =============================================================================
# ros-gz: интеграция ROS2 с Gazebo Fortress (новый Gazebo/Ignition)
# - ros-humble-ros-gz: основной пакет (gz_sim, плагины)
# - ros-humble-ros-gz-bridge: мост ROS2 ↔ Gazebo (запускается автоматически)
# - ros-humble-ros-gz-sim: запуск симулятора
#
# TurtleBot3:
# - ros-humble-turtlebot3-gazebo: миры и плагины для Gazebo Fortress
# - ros-humble-turtlebot3-description: URDF/XACRO модели роботов
#
# foxglove-bridge:
# - ros-humble-foxglove-bridge: WebSocket bridge для Python клиента
#
# Типы сообщений:
# - ros-humble-geometry-msgs: Twist для /cmd_vel
# - ros-humble-nav-msgs: Odometry для /odom
# - ros-humble-sensor-msgs: LaserScan для /scan
# =============================================================================
RUN apt-get update && apt-get install -y \
    ros-humble-ros-gz \
    ros-humble-ros-gz-bridge \
    ros-humble-ros-gz-sim \
    ros-humble-turtlebot3-gazebo \
    ros-humble-turtlebot3-description \
    ros-humble-rosbridge-suite \
    ros-humble-geometry-msgs \
    ros-humble-nav-msgs \
    ros-humble-sensor-msgs \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Настройка рабочей директории
# =============================================================================
# Здесь будут монтироваться конфигурации и миры
# =============================================================================
WORKDIR /workspace

# =============================================================================
# Копирование launch файлов и entrypoint скрипта
# =============================================================================
COPY launch/ /workspace/launch/
COPY scripts/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# =============================================================================
# Точка входа
# =============================================================================
ENTRYPOINT ["/entrypoint.sh"]
