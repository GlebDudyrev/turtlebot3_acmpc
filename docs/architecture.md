# Архитектура AC-MPC

## Обзор

AC-MPC (Actor-Critic Model Predictive Control) - это гибридный подход, сочетающий:
- **Model Predictive Control (MPC)** - оптимальное управление с учётом ограничений
- **Нейросетевое обучение** - адаптивность к сложным средам
- **Обучение с подкреплением (PPO)** - эффективное обучение политике

## Архитектура системы

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Training Loop                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐     ┌─────────────┐     ┌──────────────┐               │
│  │  Env     │────▶│  Collector  │────▶│   Buffer     │               │
│  │(Gazebo)  │     │              │     │  (Rollouts)  │               │
│  └──────────┘     └─────────────┘     └──────┬───────┘               │
│                                               │                       │
│                                               ▼                       │
│  ┌──────────┐     ┌─────────────┐     ┌──────────────┐               │
│  │  Action  │◀────│  ACMPCModel │◀────│  Train Step   │               │
│  └──────────┘     │             │     │   (PPO)       │               │
│                   └─────────────┘     └──────────────┘               │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## Компоненты AC-MPC

### 1. Neural Cost Map (Actor)

Отвечает за предсказание параметров функции стоимости MPC.

```
observation [obs_dim]
       │
       ▼
┌──────────────────┐
│   MLP Network    │
│  [128, 128, ReLU]│
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
 Q_diag    p
 [H+1, 3] [H+1, 3]
```

**Выход:**
- `Q_diag`: Диагональные элементы матрицы стоимости состояния [batch, horizon+1, n_states]
- `p`: Линейный вектор стоимости [batch, horizon+1, n_states]

**Особенности:**
- Softplus активация для Q_diag (положительно определённая матрица)
- Масштабирование p для сильного влияния на MPC

### 2. Differentiable MPC (Solver)

Дифференцируемый решатель MPC, использующий `torch.linalg.solve`.

```
x0 [batch, 3]  Q_diag [batch, H+1, 3]  p [batch, H+1, 3]
│              │                         │
▼              ▼                         ▼
┌─────────────────────────────────────────────────────┐
│                  MPC Solver                          │
│  1. Linearize Dynamics (A, B)                       │
│  2. Build QP Matrices (H, f)                        │
│  3. Solve: H @ u = -f  (torch.linalg.solve)          │
│  4. Apply Control Bounds (soft clamping)            │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
                   action [batch, 2]
```

**Особенности:**
- Полностью дифференцируем через PyTorch autograd
- Unicycle модель динамики
- Single-shooting подход

### 3. Value Network (Critic)

Оценивает ценность состояния V(s) для вычисления преимущества.

```
observation [obs_dim]
       │
       ▼
┌──────────────────┐
│   MLP Network    │
│  [128, 128, ReLU]│
│      [linear]    │
└────────┬─────────┘
         │
         ▼
       value [1]
```

### 4. TurtleBot3 Dynamics

Модель динамики робота (Unicycle):

```
x_{k+1} = x_k + v_k * cos(θ_k) * dt
y_{k+1} = y_k + v_k * sin(θ_k) * dt
θ_{k+1} = θ_k + ω_k * dt
```

**Состояние**: [x, y, θ] - позиция и ориентация
**Управление**: [v, ω] - линейная и угловая скорость

### 5. QP Builder

Построение матриц для квадратичной задачи оптимизации:

```
Cost: J = X^T Q X + U^T R U + p^T X
      где X = F @ x0 + M @ U

=> H = M^T Q M + R
=> f = 2 * M^T Q F x0 + 2 * M^T p
```

## Обучение PPO

### Rollout Collection

1. Сброс среды
2. Для каждого шага:
   - Получить наблюдение
   - Вызвать `model(obs)` → (action, value)
   - Добавить шум для исследования (ε-greedy или Normal distribution)
   - Выполнить действие в среде
   - Сохранить (obs, action, reward, value, log_prob, done)

### Advantage Estimation (GAE)

```
δ_t = r_t + γ * V(s_{t+1}) * (1 - d_t) - V(s_t)
A_t = δ_t + γ * λ * (1 - d_t) * A_{t-1}
```

### Training Step

1. Вычислить ratio = π(a|s) / π_old(a|s)
2. Clipped objective: L = -min(ratio * A, clip(ratio) * A)
3. Value loss: MSE(V(s), returns)
4. Backward pass через всю модель (полностью дифференцируемо!)

## Среда (Gymnasium)

### Observation Space (15 измерений)

```
[ lidar[10] | velocity[2] | rho | phi | yaw ]
   0-9        10-11      12    13   14
```

- **LiDAR**: Передние 180°, сгруппированные в 10 значений
- **Скорость**: Линейная и угловая скорости
- **rho**: Расстояние до цели
- **phi**: Угол до цели относительно направления робота
- **yaw**: Угол рыскания робота

### Action Space

```
[v, ω] ∈ [(-0.22, 2.84), (0.22, -2.84)]
```

### Termination

- Достигнута цель: distance < goal_threshold (0.3м)
- Столкновение: min(lidar) < 0.1м

### Truncation

- Превышено максимальное число шагов: max_steps

## ROS2 Интеграция

### Топики

| Топик | Тип | Описание |
|-------|-----|----------|
| `/scan` | LaserScan | Данные лидара |
| `/odom` | Odometry | Позиция и скорость |
| `/cmd_vel` | Twist | Управление скоростью |

### Сервисы

| Сервис | Описание |
|--------|----------|
| `/spawn_entity` | Создание объектов в Gazebo |
| `/set_entity_state` | Изменение состояния объекта |

### RosBridge

- Протокол: WebSocket
- Порт: 9090
- Библиотека: roslibpy

## Файловая структура

```
src/acmpc/
├── models/
│   ├── acmpc_model.py          # Главная модель
│   ├── cost/neural_cost_map.py # Actor
│   ├── mpc/
│   │   ├── differentiable_mpc.py # Solver
│   │   ├── dynamics.py          # Динамика робота
│   │   └── qp_builder.py       # Построение матриц
│   └── networks/value_network.py # Critic
├── training/
│   ├── ppo.py                  # PPO Trainer
│   ├── buffer.py               # Rollout Buffer
│   └── base.py                 # Интерфейс Trainer
├── training_env/
│   └── turtlebot_env.py        # Gymnasium среда
├── cases/                      # Конфигурации обучения
├── ros2/                       # ROS2 интеграция
├── registries/                 # Реестры компонентов
└── scripts/
    └── train.py                # CLI обучения
```

## Поток данных при обучении

```
1. obs = env.reset()
2. for step in n_steps:
3.     obs_tensor = torch.tensor(obs)
4.     action, value = model(obs_tensor)
5.     action = action + noise  # exploration
6.     next_obs, reward, done, _, _ = env.step(action)
7.     buffer.add(obs, action, reward, value, log_prob, done)
8.     obs = next_obs
9. 
10. advantages = compute_gae(buffer)
11. for epoch in n_epochs:
12.     for sample in buffer:
13.         mpc_action, value = model(sample.obs)
14.         loss = ppo_loss(mpc_action, sample.action, advantages)
15.         loss.backward()
16.     optimizer.step()
```
