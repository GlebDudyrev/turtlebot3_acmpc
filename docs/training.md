# Руководство по обучению

## Быстрый старт

### Предварительные требования

1. Установленный Docker и Docker Compose
2. Python 3.10+
3. Gazebo Classic 11 (для визуализации)

### Шаг 1: Запуск симуляции

```bash
cd docker
docker-compose up -d
```

Проверить статус:
```bash
docker-compose ps
```

### Шаг 2: Запуск обучения

```bash
# Использование CLI
acmpc train --case nav_obstacles_basic

# Или через Python
python -m acmpc.scripts.train --case nav_obstacles_basic
```

### Шаг 3: Мониторинг

```bash
# TensorBoard
tensorboard --logdir experiments/
```

Открыть http://localhost:6006 в браузере.

## Процесс обучения

### Инициализация

1. Загрузка конфигурации случая
2. Создание модели AC-MPC
3. Создание среды Gymnasium
4. Инициализация PPO тренера

### Основной цикл

```
for epoch in range(max_epochs):
    # 1. Сбор rollout данных
    rollout_metrics = trainer.collect_rollouts(env)
    
    # 2. Обучение модели
    train_metrics = trainer.train_step()
    
    # 3. Логирование
    writer.add_scalar(...)
    
    # 4. Оценка (каждые eval_freq эпох)
    if epoch % eval_freq == 0:
        eval_metrics = trainer.evaluate()
    
    # 5. Сохранение чекпоинта (каждые save_freq эпох)
    if epoch % save_freq == 0:
        trainer.save_checkpoint(...)
```

### Rollout Collection

```
obs, _ = env.reset()

for step in n_steps:
    obs_tensor = torch.tensor(obs)
    action, log_prob, value = trainer.sample_action(obs_tensor)
    
    next_obs, reward, terminated, truncated, _ = env.step(action)
    
    buffer.add(obs, action, reward, value, log_prob, done)
    
    if terminated or truncated:
        obs, _ = env.reset()
    else:
        obs = next_obs
```

### Training Step

1. **Вычисление GAE**: Расчёт преимуществ с использованием Generalized Advantage Estimation
2. **PPO Update**: Несколько эпох обучения на буфере
3. **Обновление exploration std**: Линейное уменьшение стандартного отклонения

## Структура эксперимента

После запуска обучения создаётся директория:

```
experiments/
└── nav_obstacles_basic/
    └── 2024-01-01_12-00-00/
        ├── config.yaml       # Конфигурация
        ├── logs/             # TensorBoard логи
        │   └── events.*
        └── checkpoints/      # Чекпоинты
            ├── epoch_50.pt
            ├── epoch_100.pt
            └── final.pt
```

## Продвинутое использование

### Возобновление обучения

```bash
acmpc train --case nav_obstacles_basic --resume experiments/.../checkpoints/epoch_100.pt
```

### Кастомный случай

```python
from acmpc.cases.configs import CaseConfig, EnvConfig, ACMPCConfig, PPOConfig
from acmpc.cases import Case
from acmpc.cases.registry import CaseRegistryInstance

config = CaseConfig(
    name="my_custom_case",
    description="Custom training configuration",
    env=EnvConfig(
        robot_name="waffle",
        reward_fn="basic_reward",
        goal_max_distance=5.0,
    ),
    acmpc=ACMPCConfig(
        mpc=MPCConfig(horizon=20),
    ),
    ppo=PPOConfig(
        n_steps=4096,
        learning_rate=1e-4,
    ),
    max_epochs=2000,
)

my_case = Case(name="my_custom_case", config=config)
CaseRegistryInstance.register("my_custom_case", my_case)
```

### Запуск через Python

```python
import torch
from acmpc.cases import get_case
from acmpc.training.ppo import PPOTrainer
from acmpc.training_env import make as make_env

# Получить случай
case = get_case("nav_obstacles_basic")

# Создать среду
env = make_env(case)

# Создать тренера
device = "cuda" if torch.cuda.is_available() else "cpu"
trainer = PPOTrainer.from_case(case.config, device=device)

# Обучение
for epoch in range(case.config.max_epochs):
    rollout_metrics = trainer.collect_rollouts(env)
    train_metrics = trainer.train_step()
    
    if epoch % 10 == 0:
        print(f"Epoch {epoch}: reward={rollout_metrics['rollout_reward']:.2f}")
```

## Устранение проблем

### Docker контейнер не запускается

```bash
# Проверить логи
docker-compose logs

# Пересобрать образ
docker-compose build --no-cache
```

### Ошибка подключения к rosbridge

```bash
# Проверить что контейнер запущен
docker-compose ps

# Проверить порт
netstat -tuln | grep 9090

# Перезапустить
docker-compose restart
```

### Обучение не сходится

Попробуйте:
- Уменьшить learning_rate
- Увеличить n_steps
- Изменить функцию награды
- Увеличить горизонт MPC

### GPU не используется

```bash
# Проверить доступность CUDA
python -c "import torch; print(torch.cuda.is_available())"

# Явно указать device
trainer = PPOTrainer.from_case(config, device="cuda")
```

## Лучшие практики

1. **Начните с small**: Тестируйте на коротких эпизодах (max_steps=100)
2. **Логируйте метрики**: Используйте TensorBoard для мониторинга
3. **Сохраняйте чекпоинты**: Регулярно сохраняйте для возобновления
4. **Валидируйте**: Оценивайте модель отдельно от обучения
5. **Воспроизводимость**: Используйте seed для повторяемости

## Мониторинг метрик

### Ключевые метрики

| Метрика | Описание | Ожидаемое поведение |
|---------|----------|---------------------|
| rollout_reward | Средняя награда за эпизод | Увеличивается |
| policy_loss | Loss политики PPO | Уменьшается |
| value_loss | Loss функции ценности | Уменьшается |
| exploration_std | Std исследования | Уменьшается |
| clip_fraction | Доля клиппинга | ~0.1-0.3 |

### Графики TensorBoard

- `train/policy_loss` - Loss политики
- `train/value_loss` - Loss критика
- `train/exploration_std` - Исследование
- `rollout/rollout_reward` - Награда за rollout
- `eval/eval_reward` - Оценочная награда
