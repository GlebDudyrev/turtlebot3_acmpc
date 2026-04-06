# turtlebot3_acmpc

AC-MPC (Actor-Critic Model Predictive Control) implementation for TurtleBot3 navigation using PPO reinforcement learning.

## Описание

Проект реализует алгоритм обучения с подкреплением AC-MPC для навигации робота TurtleBot3 в среде с препятствиями. AC-MPC сочетает в себе преимущества Model Predictive Control (MPC) с нейросетевым обучением:

- **Actor (Neural Cost Map)**: Нейросеть, которая предсказывает параметры функции стоимости для MPC
- **Critic (Value Network)**: Оценивает ценность состояния для вычисления преимущества (advantage)
- **Solver (Differentiable MPC)**: Дифференцируемый решатель MPC, полностью интегрированный в граф PyTorch

## Как это работает

```
observation → NeuralCostMap → (Q_diag, p) → DifferentiableMPC → action
observation → ValueNetwork → V(s)
```

1. **Наблюдение**: Лидар (10 значений) + скорости + полярные координаты цели + угол рыскания
2. **Neural Cost Map**: MLP сеть предсказывает диагональные элементы матрицы стоимости Q и линейный вектор p
3. **MPC Solver**: Использует `torch.linalg.solve` для решения квадратичной задачи оптимизации - полностью дифференцируемо
4. **PPO**: Обучает сеть стоимости и сеть ценности с использованием GAE (Generalized Advantage Estimation)

## Установка

### Требования

- Python 3.10+
- Docker и Docker Compose
- Ubuntu 22.04 (рекомендуется)

### Установка пакета

```bash
# Клонировать репозиторий
git clone https://github.com/GlebDudyrev/turtlebot3_acmpc.git
cd turtlebot3_acmpc

# Создать и активировать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -e ".[dev]"

# Или установить основные зависимости
pip install -e .
```

## Быстрый старт

### 1. Запуск симуляции

```bash
cd docker
docker-compose up -d
```

Это запустит:
- Gazebo с TurtleBot3
- rosbridge_server на порту 9090

Для визуализации на хосте:
```bash
gzclient
```

### 2. Запуск обучения

```bash
# Обучение с базовой конфигурацией
acmpc train --case nav_obstacles_basic

# Или через Python
python -m acmpc.scripts.train --case nav_obstacles_basic
```

### 3. Мониторинг

```bash
# TensorBoard
tensorboard --logdir experiments/
```

## Доступные случаи (Cases)

| Имя | Описание |
|-----|----------|
| `nav_obstacles_basic` | Навигация с базовой функцией награды |
| `nav_obstacles` | Навигация с плотной функцией награды |
| `nav_obstacles_advanced` | Навигация с продвинутой функцией награды |

## Реализованные компоненты

### Ядро AC-MPC
- [x] Neural Cost Map (Actor)
- [x] Differentiable MPC Solver
- [x] Value Network (Critic)
- [x] TurtleBot3 Dynamics (Unicycle model)
- [x] QP Builder для MPC

### Обучение PPO
- [x] Rollout Buffer с GAE
- [x] PPO Trainer с clipped surrogate objective
- [x] Exploration с уменьшающимся std
- [x] TensorBoard логирование
- [x] Сохранение/загрузка чекпоинтов

### Среда (Gymnasium)
- [x] ROS2/rosbridge интеграция
- [x] Подписки: /scan, /odom
- [x] Публикации: /cmd_vel
- [x] Сервисы: spawn_entity, set_entity_state

### Реестры (Registries)
- [x] Robot Parameters (burger, waffle, waffle_pi)
- [x] Reward Functions (basic_reward, dense_goal, advanced_reward)
- [x] Cases

### Docker
- [x] docker-compose.yml с Gazebo + TurtleBot3
- [x] rosbridge_server интеграция

## Предстоит сделать

- [ ] Реализация полной функции награды dense_goal_reward
- [ ] Реализация advanced_reward функции
- [ ] Улучшенная визуализация в TensorBoard
- [ ] Тестирование и валидация обучения
- [ ] Интеграция с реальным роботом
- [ ] Web UI для мониторинга
- [ ] ROS 2 package.xml для интеграции в ROS

## Структура проекта

```
turtlebot3_acmpc/
├── src/acmpc/
│   ├── models/
│   │   ├── acmpc_model.py      # Главная модель AC-MPC
│   │   ├── cost/
│   │   │   └── neural_cost_map.py  # Actor
│   │   ├── mpc/
│   │   │   ├── differentiable_mpc.py  # Дифференцируемый MPC
│   │   │   ├── dynamics.py        # Модель динамики
│   │   │   └── qp_builder.py     # Построение матриц QP
│   │   └── networks/
│   │       └── value_network.py  # Critic
│   ├── training/
│   │   ├── ppo.py               # PPO Trainer
│   │   ├── buffer.py            # Rollout Buffer
│   │   └── base.py              # BaseTrainer интерфейс
│   ├── training_env/
│   │   └── turtlebot_env.py     # Gymnasium среда
│   ├── cases/
│   │   ├── case.py              # Case модель
│   │   ├── registry.py          # Реестр случаев
│   │   ├── configs/             # Конфигурации
│   │   └── cases/               # Зарегистрированные случаи
│   ├── ros2/                    # ROS2 интеграция
│   │   ├── client.py            # RosBridge клиент
│   │   ├── topics/              # Топики (scan, odom, cmd_vel)
│   │   └── services/            # Сервисы
│   ├── registries/              # Реестры
│   │   ├── robots/              # Параметры роботов
│   │   └── rewards/             # Функции награды
│   └── scripts/
│       └── train.py             # Скрипт обучения
├── docker/                      # Docker конфигурация
├── configs/                    # Конфигурации миров
├── tests/                       # Тесты
└── docs/                        # Документация
```

## Конфигурация

Основные параметры в `CaseConfig`:

```python
CaseConfig(
    name="my_case",
    env=EnvConfig(
        robot_name="burger",        # Модель робота
        reward_fn="basic_reward",   # Функция награды
        goal_threshold=0.3,        # Достижение цели
        max_steps=500,             # Макс. шагов в эпизоде
    ),
    acmpc=ACMPCConfig(
        cost_map=CostMapConfig(
            hidden_layers=[128, 128],
        ),
        mpc=MPCConfig(
            horizon=15,             # Горизонт MPC
        ),
        value_network=ValueNetworkConfig(
            hidden_layers=[128, 128],
        ),
    ),
    ppo=PPOConfig(
        learning_rate=3e-4,
        n_steps=2048,
        clip_range=0.2,
    ),
    max_epochs=1000,
)
```

## Разработка

```bash
# Запуск тестов
pytest

# Линтинг
ruff check .
mypy src/

# Форматирование
black src/ tests/
```

## Лицензия

MIT License - см. файл LICENSE
