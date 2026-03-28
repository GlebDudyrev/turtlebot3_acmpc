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
TURTLEBOT3_MODEL="${TURTLEBOT3_MODEL:-burger}"

log_info "Starting TurtleBot3 AC-MPC environment"
log_info "World: ${WORLD_NAME}"
log_info "Model: ${TURTLEBOT3_MODEL}"

source /opt/ros/humble/setup.bash

export TURTLEBOT3_MODEL

export GAZEBO_MODEL_PATH=/opt/ros/humble/share/turtlebot3_gazebo/models:$GAZEBO_MODEL_PATH

source /usr/share/gazebo/setup.sh

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

log_info "Starting Gazebo simulation with TurtleBot3..."

ros2 launch turtlebot3_gazebo turtlebot3_world.launch.py \
    world_file:="${WORLD_PATH}" \
    model:="${TURTLEBOT3_MODEL}" \
    use_sim_time:=true &
GAZEBO_PID=$!

sleep 8

if ! kill -0 $GAZEBO_PID 2>/dev/null; then
    log_error "Gazebo failed to start"
    exit 1
fi

log_info "Starting rosbridge_server on port 9090..."
ros2 run rosbridge_server rosbridge_websocket.py &
ROSBRIDGE_PID=$!

sleep 2

log_info "All services started successfully!"
log_info "rosbridge WebSocket: ws://localhost:9090"
log_info "Gazebo: connect from host using GAZEBO_MASTER_URI=http://localhost:11345"
log_info "ROS2 topics: /scan, /odom, /cmd_vel, /tf"
log_info "Press Ctrl+C to stop"

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
