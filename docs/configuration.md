# Конфигурация

## Обзор

Проект использует систему конфигураций на основе Pydantic для строгой валидации и автодокументации.

## Структура конфигурации

```
CaseConfig
├── EnvConfig          # Параметры среды
├── ACMPCConfig       # Параметры AC-MPC модели
│   ├── CostMapConfig     # Neural Cost Map (Actor)
│   ├── MPCConfig         # Differentiable MPC
│   └── ValueNetworkConfig # Value Network (Critic)
├── PPOConfig         # Гиперпараметры PPO
└── General settings  # device, seed, max_epochs и т.д.
```

## EnvConfig

Параметры окружающей среды и робота.

```python
from acmpc.cases.configs import EnvConfig

config = EnvConfig(
    world_name="turtlebot3_empty",     # Имя мира Gazebo
    robot_name="burger",                # burger, waffle, waffle_pi
    reward_fn="basic_reward",           # Функция награды
    goal_threshold=0.3,                 # Дистанция достижения цели (м)
    goal_min_distance=1.0,              # Мин. дистанция до цели
    goal_max_distance=3.0,              # Макс. дистанция до цели
    max_steps=500,                      # Макс. шагов в эпизоде
    dt=0.1,                             # Шаг симуляции (с)
)
```

###robot_name

Модель робота. Влияет на:
- Максимальные скорости
- Параметры лидара
- Размеры робота

| Модель | max_linear_vel | max_angular_vel | lidar_range |
|--------|----------------|-----------------|-------------|
| burger | 0.22 м/с | 2.84 рад/с | 3.5 м |
| waffle | 0.26 м/с | 1.82 рад/с | 3.5 м |
| waffle_pi | 0.26 м/с | 1.82 рад/с | 3.5 м |

### reward_fn

Функция награды из реестра:
- `basic_reward` - базовая функция из статьи
- `dense_goal` - плотная награда (заглушка)
- `advanced_reward` - продвинутая награда

## ACMPCConfig

Параметры компонентов AC-MPC.

```python
from acmpc.cases.configs import ACMPCConfig, CostMapConfig, MPCConfig, ValueNetworkConfig

config = ACMPCConfig(
    cost_map=CostMapConfig(
        matrix_type="diagonal",    # diagonal, cholesky, full
        hidden_layers=[128, 128],   # Размеры скрытых слоёв
        activation="relu",          # relu, tanh, elu
    ),
    mpc=MPCConfig(
        horizon=15,                # Горизонт предсказания MPC
        solver_type="osqp",         # osqp или qp
    ),
    value_network=ValueNetworkConfig(
        hidden_layers=[128, 128],  # Размеры скрытых слоёв
        activation="relu",          # relu, tanh, elu
    ),
)
```

### CostMapConfig

Neural Cost Map (Actor) предсказывает параметры функции стоимости MPC.

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| matrix_type | str | "diagonal" | Тип матрицы стоимости |
| hidden_layers | list[int] | [128, 128] | Размеры скрытых слоёв MLP |
| activation | str | "relu" | Функция активации |

### MPCConfig

Differentiable MPC решатель.

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| horizon | int | 15 | Горизонт предсказания |
| solver_type | str | "osqp" | Тип решателя QP |

### ValueNetworkConfig

Value Network (Critic) оценивает V(s).

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| hidden_layers | list[int] | [128, 128] | Размеры скрытых слоёв |
| activation | str | "relu" | Функция активации |

## PPOConfig

Гиперпараметры алгоритма PPO.

```python
from acmpc.cases.configs import PPOConfig

config = PPOConfig(
    learning_rate=3e-4,         # Скорость обучения
    n_steps=2048,               # Шагов сбора данных
    batch_size=64,               # Размер батча
    n_epochs=10,                 # Эпох обучения на буфер
    gamma=0.99,                  # Коэффициент дисконтирования
    gae_lambda=0.95,             # Параметр GAE
    clip_range=0.2,              # Диапазон клиппинга PPO
    ent_coef=0.01,               # Коэффициент энтропии
    vf_coef=0.5,                 # Коэффициент функции ценности
    max_grad_norm=0.5,            # Максимальная норма градиента
    exploration_max_std=0.1,     # Макс. std исследования
    exploration_min_std=0.0,     # Мин. std исследования
    exploration_epochs=100,       # Эпох линейного затухания std
)
```

### Объяснение параметров

| Параметр | Описание | Рекомендуемый диапазон |
|----------|----------|------------------------|
| learning_rate | Скорость обучения Adam | 1e-4 - 1e-3 |
| n_steps | Шагов между обновлениями | 1024 - 4096 |
| n_epochs | Проходов по буферу | 4 - 10 |
| gamma | Дисконтирование наград | 0.99 - 0.999 |
| gae_lambda | Параметр GAE (bias/variance tradeoff) | 0.9 - 0.99 |
| clip_range | Клиппинг ratio в PPO | 0.1 - 0.3 |
| exploration_std | Std нормального шума для исследования | 0.05 - 0.2 |

## CaseConfig

Полная конфигурация случая обучения.

```python
from acmpc.cases.configs import CaseConfig, EnvConfig, ACMPCConfig, PPOConfig

case_config = CaseConfig(
    name="my_experiment",
    description="My custom training case",
    
    env=EnvConfig(...),
    acmpc=ACMPCConfig(...),
    ppo=PPOConfig(...),
    
    device="auto",      # cpu, cuda, auto
    seed=42,            # Seed для воспроизводимости
    max_epochs=1000,    # Макс. эпох обучения
    eval_freq=10,       # Частота оценки (эпохи)
    save_freq=50,       # Частота сохранения чекпоинтов
)
```

## Случаи (Cases)

Зарегистрированные случаи обучения.

### nav_obstacles_basic

```python
Case(
    name="nav_obstacles_basic",
    description="Navigation with obstacles - basic reward",
    config=CaseConfig(
        name="nav_obstacles_basic",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="basic_reward",
        ),
    ),
)
```

### nav_obstacles

```python
Case(
    name="nav_obstacles",
    description="Navigation with obstacles",
    config=CaseConfig(
        name="nav_obstacles",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="dense_goal",
        ),
    ),
)
```

### nav_obstacles_advanced

```python
Case(
    name="nav_obstacles_advanced",
    description="Navigation with obstacles - advanced reward",
    config=CaseConfig(
        name="nav_obstacles_advanced",
        env=EnvConfig(
            robot_name="burger",
            reward_fn="advanced_reward",
        ),
    ),
)
```

## Функции награды

### basic_reward

Базовая функция награды из статьи:

```python
r(st, at) = {
    r_arrive  если d_t < c_d (достигнута цель)
    r_collision если max(x_t) < c_o (столкновение)
    c_r * (d_{t-1} - d_t) иначе (прогресс к цели)
}
```

Параметры:
- `c_d = 0.3` - порог достижения цели
- `c_o = 0.1` - порог столкновения
- `r_arrive = 100.0` - награда за достижение
- `r_collision = -100.0` - штраф за столкновение
- `c_r = 10.0` - коэффициент прогресса

## Примеры конфигураций

### Быстрое тестирование

```python
CaseConfig(
    name="test",
    env=EnvConfig(max_steps=100),
    ppo=PPOConfig(n_steps=128, max_epochs=5),
    max_epochs=10,
)
```

### Высокое качество

```python
CaseConfig(
    name="high_quality",
    env=EnvConfig(goal_max_distance=5.0, max_steps=1000),
    ppo=PPOConfig(n_steps=4096, n_epochs=20),
    acmpc=ACMPCConfig(
        mpc=MPCConfig(horizon=25),
        cost_map=CostMapConfig(hidden_layers=[256, 256, 256]),
    ),
    max_epochs=5000,
)
```

### GPU обучение

```python
CaseConfig(
    name="gpu_training",
    device="cuda",  # Использовать GPU если доступен
    ppo=PPOConfig(learning_rate=1e-3, batch_size=256),
    max_epochs=2000,
)
```
