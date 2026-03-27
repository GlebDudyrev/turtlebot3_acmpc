#!/bin/bash
# =============================================================================
# Entrypoint for TurtleBot3 AC-MPC Docker container
# =============================================================================
# Запускает симуляцию TurtleBot3 в Gazebo Fortress:
# - Gazebo Fortress (gzserver)
# - TurtleBot3 robot spawn
# - ros_gz_bridge (автоматически через turtlebot3_gazebo)
# - rosbridge_server (WebSocket для Python на хосте)
# =============================================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

WORLD_NAME="${WORLD_NAME:-turtlebot3_empty}"

log_info "Starting TurtleBot3 AC-MPC environment"
log_info "World: ${WORLD_NAME}"
log_info "Model: ${TURTLEBOT3_MODEL:-burger}"

# Source ROS2
source /opt/ros/humble/setup.bash

# Set TurtleBot3 model
export TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"

# Find world file
find_world() {
    local world_name="$1"
    
    if [[ -f "/workspace/worlds/${world_name}.world" ]]; then
        echo "/workspace/worlds/${world_name}.world"
        return 0
    fi
    
    if [[ -f "/opt/ros/humble/share/turtlebot3_gazebo/worlds/${world_name}.world" ]]; then
        echo "/opt/ros/humble/share/turtlebot3_gazebo/worlds/${world_name}.world"
        return 0
    fi
    
    return 1
}

WORLD_PATH=$(find_world "${WORLD_NAME}") || {
    log_error "World not found: ${WORLD_NAME}"
    exit 1
}

log_info "World path: ${WORLD_PATH}"

# =============================================================================
# Start Gazebo simulation with TurtleBot3 (headless - no GUI)
# =============================================================================
# Используем headless launch файл (без gzclient)
# Автоматически запускает:
# - gzserver (Gazebo Fortress)
# - spawn_turtlebot3.launch.py
# - ros_gz_bridge for /scan, /odom, /cmd_vel, /tf, /imu
# =============================================================================
log_info "Starting Gazebo simulation with TurtleBot3 (headless)..."
ros2 launch /workspace/launch/turtlebot3_headless.launch.py &
GAZEBO_PID=$!

# Wait for simulation to start
sleep 5

# =============================================================================
# Start rosbridge_server (WebSocket for Python on host)
# =============================================================================
# Port 9090 - rosbridge WebSocket
# Allows Python code on host to connect without installing ROS2
# =============================================================================
log_info "Starting rosbridge_server on port 9090..."
ros2 run rosbridge_server rosbridge_websocket.py &
ROSBRIDGE_PID=$!

sleep 2

# =============================================================================
# Info
# =============================================================================
log_info "All services started successfully!"
log_info "rosbridge WebSocket: ws://localhost:9090"
log_info "Gazebo Web: https://app.gazebosim.org → ws://localhost:9002"
log_info "ROS2 topics: /scan, /odom, /cmd_vel, /tf, /imu"
log_info "Press Ctrl+C to stop"

# =============================================================================
# Wait for shutdown
# =============================================================================
cleanup() {
    log_info "Shutting down..."
    [[ -n "${ROSBRIDGE_PID}" ]] && kill ${ROSBRIDGE_PID} 2>/dev/null
    [[ -n "${GAZEBO_PID}" ]] && kill ${GAZEBO_PID} 2>/dev/null
    kill -- -$$ 2>/dev/null
    log_info "Shutdown complete"
    exit 0
}

trap cleanup SIGTERM SIGINT

wait
