# API Reference

## Модели AC-MPC

### ACMPCModel

Главная модель AC-MPC, объединяющая Neural Cost Map, Differentiable MPC и Value Network.

```python
from acmpc.models import ACMPCModel

model = ACMPCModel(
    obs_dim=15,                 # Размер наблюдения
    n_states=3,                 # x, y, theta
    horizon=15,                 # Горизонт MPC
    cost_map_hidden_layers=[128, 128],
    value_hidden_layers=[128, 128],
    mpc_horizon=15,
    mpc_dt=0.1,
    mpc_control_bounds=(-0.22, 0.22),
)

action, value = model(obs)
# action: [batch, 2] - [v, omega]
# value:  [batch, 1] - V(s)
```

### NeuralCostMap

Neural Cost Map - Actor сеть, предсказывающая параметры функции стоимости MPC.

```python
from acmpc.models.cost import NeuralCostMap

cost_map = NeuralCostMap(
    obs_dim=15,
    n_states=3,
    horizon=15,
    hidden_layers=[128, 128],
)

Q_diag, p = cost_map(obs)
# Q_diag: [batch, horizon+1, n_states]
# p:      [batch, horizon+1, n_states]
```

### DifferentiableMPC

Дифференцируемый решатель MPC.

```python
from acmpc.models.mpc import DifferentiableMPC

mpc = DifferentiableMPC(
    horizon=15,
    dt=0.1,
    control_bounds=(-0.22, 0.22),
)

action = mpc(x0, Q_diag, p)
# x0:     [batch, n_states]
# Q_diag: [batch, horizon+1, n_states]
# p:      [batch, horizon+1, n_states]
# action: [batch, n_controls]
```

### ValueNetwork

Value Network - Critic сеть для оценки V(s).

```python
from acmpc.models.networks import ValueNetwork

value_net = ValueNetwork(
    obs_dim=15,
    hidden_layers=[128, 128],
)

value = value_net(obs)
# obs:   [batch, obs_dim]
# value: [batch, 1]
```

### TurtleBot3Dynamics

Модель динамики робота (Unicycle).

```python
from acmpc.models.mpc.dynamics import TurtleBot3Dynamics

dynamics = TurtleBot3Dynamics(dt=0.1)

# Предсказание следующего состояния
next_state = dynamics.forward(state, control)
# state:   [batch, 3]
# control: [batch, 2]
# next_state: [batch, 3]

# Линеаризация
A, B = dynamics.linearize(state, control)
# A: [batch, 3, 3]
# B: [batch, 3, 2]
```

## Обучение

### PPOTrainer

Тренер PPO для AC-MPC.

```python
from acmpc.training.ppo import PPOTrainer

trainer = PPOTrainer(
    model=acmpc_model,
    ppo_config=ppo_config,
    acmpc_config=acmpc_config,
    env_config=env_config,
    case=case,
    device="cpu",
)

# Сбор rollout данных
metrics = trainer.collect_rollouts(env)

# Обучение
train_metrics = trainer.train_step()

# Оценка
eval_metrics = trainer.evaluate()

# Сохранение/загрузка чекпоинта
trainer.save_checkpoint("checkpoint.pt")
trainer.load_checkpoint("checkpoint.pt")

# Создание из конфигурации
trainer = PPOTrainer.from_case(case_config, device="cuda")
```

### RolloutBuffer

Буфер для хранения траекторий и вычисления GAE.

```python
from acmpc.training.buffer import RolloutBuffer

buffer = RolloutBuffer(
    obs_dim=15,
    action_dim=2,
    n_steps=2048,
    gamma=0.99,
    gae_lambda=0.95,
    device="cpu",
)

# Добавление перехода
buffer.add(obs, action, reward, value, log_prob, done)

# Вычисление преимуществ
buffer.compute_advantages(final_value)

# Получение данных
observations, actions, advantages, returns, old_log_probs, values = buffer.get()

# Сброс
buffer.reset()
```

## Среда

### TurtleBotEnv

Gymnasium среда для TurtleBot3.

```python
from acmpc.training_env import make as make_env

env = make_env(case)

# Сброс среды
observation, info = env.reset()

# Шаг
observation, reward, terminated, truncated, info = env.step(action)

# observation: [15] - массив numpy
# reward: float
# terminated: bool
# truncated: bool
# info: dict
```

### Observation Space

```
[ lidar[10] | velocity[2] | rho | phi | yaw ]
   0-9        10-11      12    13   14

lidar:    Обработанные данные лидара (передние 180°, 10 значений)
velocity: [linear_vel, angular_vel]
rho:      Расстояние до цели
phi:      Угол до цели
yaw:      Угол рыскания робота
```

### Action Space

```
[v, omega] ∈ [(-0.22, 2.84), (0.22, -2.84)]

v:      Линейная скорость (м/с)
omega:  Угловая скорость (рад/с)
```

## Конфигурация

### CaseConfig

```python
from acmpc.cases.configs import CaseConfig

config = CaseConfig(
    name="my_case",
    description="Description",
    env=EnvConfig(...),
    acmpc=ACMPCConfig(...),
    ppo=PPOConfig(...),
    device="auto",
    seed=42,
    max_epochs=1000,
    eval_freq=10,
    save_freq=50,
)
```

### EnvConfig

```python
from acmpc.cases.configs import EnvConfig

config = EnvConfig(
    world_name="turtlebot3_empty",
    robot_name="burger",
    reward_fn="basic_reward",
    goal_threshold=0.3,
    goal_min_distance=1.0,
    goal_max_distance=3.0,
    max_steps=500,
    dt=0.1,
)
```

### ACMPCConfig

```python
from acmpc.cases.configs import ACMPCConfig

config = ACMPCConfig(
    cost_map=CostMapConfig(...),
    mpc=MPCConfig(...),
    value_network=ValueNetworkConfig(...),
)
```

### PPOConfig

```python
from acmpc.cases.configs import PPOConfig

config = PPOConfig(
    learning_rate=3e-4,
    n_steps=2048,
    batch_size=64,
    n_epochs=10,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    ent_coef=0.01,
    vf_coef=0.5,
    max_grad_norm=0.5,
    exploration_max_std=0.1,
    exploration_min_std=0.0,
    exploration_epochs=100,
)
```

## Реестры

### Получение случая

```python
from acmpc.cases import get_case, list_cases

# Список доступных случаев
cases = list_cases()
# ['nav_obstacles_basic', 'nav_obstacles', 'nav_obstacles_advanced']

# Получение случая
case = get_case("nav_obstacles_basic")
```

### Получение параметров робота

```python
from acmpc.registries.robots import RobotParamsRegistry

params = RobotParamsRegistry.get("burger")
# RobotParams(
#     name="TurtleBot3 Burger",
#     max_linear_vel=0.22,
#     max_angular_vel=2.84,
#     ...
# )
```

### Получение функции награды

```python
from acmpc.registries.rewards import RewardRegistry

reward_fn = RewardRegistry.get("basic_reward")
reward = reward_fn(info)
```

## ROS2 Интеграция

### RosBridgeClient

```python
from acmpc.ros2 import RosBridgeClient

client = RosBridgeClient(host="localhost", port=9090)
client.run()

# Ожидание подключения
while not client.is_connected:
    time.sleep(0.1)

# Отключение
client.disconnect()
```

### Топики

```python
from acmpc.ros2.topics import LaserScanSubscriber, OdomSubscriber, CmvVelPublisher

# Подписка на LaserScan
scan = LaserScanSubscriber(client, callback)
scan.subscribe()

# Подписка на Odometry
odom = OdomSubscriber(client, callback)
odom.subscribe()

# Публикация cmd_vel
cmd_vel = CmvVelPublisher(client)
cmd_vel.publish(linear_vel=0.1, angular_vel=0.0)
```

### Сервисы

```python
from acmpc.ros2.services import SpawnEntityServiceClient, SetEntityStateServiceClient

# Создание сущности
spawn = SpawnEntityServiceClient(client)
spawn.call(name="my_robot", xml=sdf_string, position=(0, 0, 0))

# Изменение состояния
set_state = SetEntityStateServiceClient(client)
set_state.call(name="robot_name", position=(1, 0, 0))
```

## CLI

### train

```bash
acmpc train --case nav_obstacles_basic --resume checkpoint.pt
```

Аргументы:
- `--case` - Имя случая из реестра
- `--resume` - Путь к чекпоинту для возобновления
- `--start-containers` - Автозапуск Docker контейнеров (по умолчанию: True)

## Примеры

### Создание модели и выполнение forward pass

```python
import torch
from acmpc.models import ACMPCModel

model = ACMPCModel(obs_dim=15, n_states=3, horizon=15)

obs = torch.randn(1, 15)  # [batch=1, obs_dim]
action, value = model(obs)

print(f"Action shape: {action.shape}")  # [1, 2]
print(f"Value shape: {value.shape}")    # [1, 1]
```

### Создание кастомной функции награды

```python
from acmpc.registries.rewards import RewardRegistry

@RewardRegistry.register("my_reward")
def my_reward(info: dict) -> float:
    distance = info.get("distance_to_goal", float("inf"))
    progress = info.get("prev_distance", distance) - distance
    
    # Награда за прогресс
    reward = 10.0 * progress
    
    # Штраф за столкновение
    if info.get("min_lidar", float("inf")) < 0.1:
        reward -= 100.0
    
    # Награда за достижение цели
    if distance < 0.3:
        reward += 100.0
    
    return reward
```

### Создание кастомного случая

```python
from acmpc.cases import Case
from acmpc.cases.configs import CaseConfig, EnvConfig
from acmpc.cases.registry import CaseRegistryInstance

my_case = Case(
    name="my_case",
    description="My custom case",
    config=CaseConfig(
        name="my_case",
        env=EnvConfig(
            robot_name="waffle",
            reward_fn="my_reward",
        ),
    ),
)

CaseRegistryInstance.register("my_case", my_case)
```
