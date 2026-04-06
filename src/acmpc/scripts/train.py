"""AC-MPC training script with CLI."""

from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import tyro
import torch
from torch.utils.tensorboard import SummaryWriter

from acmpc.cases import get_case, list_cases
from acmpc.training.ppo import PPOTrainer
from acmpc.training_env import make as make_env

DOCKER_DIR = Path(__file__).parent.parent.parent.parent / "docker"
EXPERIMENTS_DIR = Path("experiments")
ROSBRIDGE_HOST = "localhost"
ROSBRIDGE_PORT = 9090
ROSBRIDGE_TIMEOUT = 60


def wait_for_rosbridge(
    host: str = ROSBRIDGE_HOST,
    port: int = ROSBRIDGE_PORT,
    timeout: int = ROSBRIDGE_TIMEOUT,
) -> bool:
    """Wait for rosbridge to be ready."""
    import socket

    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((host, port))
            sock.close()
            if result == 0:
                print(f"Rosbridge ready at {host}:{port}")
                return True
        except socket.error:
            pass
        time.sleep(1)

    print(f"Timeout waiting for rosbridge at {host}:{port}")
    return False


def start_docker_compose() -> subprocess.CompletedProcess:
    """Start docker-compose services."""
    print("Starting Docker containers...")
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        cwd=str(DOCKER_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error starting docker-compose: {result.stderr}")
        sys.exit(1)
    print("Docker containers started")
    return result


def stop_docker_compose() -> None:
    """Stop docker-compose services."""
    print("Stopping Docker containers...")
    result = subprocess.run(
        ["docker-compose", "down"],
        cwd=str(DOCKER_DIR),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Warning: Error stopping docker-compose: {result.stderr}")
    else:
        print("Docker containers stopped")


def create_experiment_dir(case_name: str) -> Path:
    """Create experiment directory with timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    exp_dir = EXPERIMENTS_DIR / case_name / timestamp
    exp_dir.mkdir(parents=True, exist_ok=True)

    (exp_dir / "logs").mkdir(exist_ok=True)
    (exp_dir / "checkpoints").mkdir(exist_ok=True)

    return exp_dir


def save_config(exp_dir: Path, case) -> None:
    """Save case config to experiment directory."""
    config_path = exp_dir / "config.yaml"
    import json

    config_dict = case.config.model_dump()

    # Convert to JSON-serializable format
    def convert_value(v):
        if hasattr(v, "model_dump"):
            return convert_value(v.model_dump())
        elif isinstance(v, dict):
            return {k: convert_value(val) for k, val in v.items()}
        elif isinstance(v, list):
            return [convert_value(item) for item in v]
        else:
            return v

    config_dict = convert_value(config_dict)

    with open(config_path, "w") as f:
        json.dump(config_dict, f, indent=2)
    print(f"Config saved to {config_path}")


def train(
    case: str = "nav_obstacles_basic",
    resume: str | None = None,
    start_containers: bool = True,
) -> None:
    """Train AC-MPC model.

    Args:
        case: Case name from registry
        resume: Path to checkpoint to resume from
        start_containers: Whether to start docker containers automatically
    """
    # Validate case
    available_cases = list_cases()
    if case not in available_cases:
        print(f"Error: Case '{case}' not found. Available: {available_cases}")
        sys.exit(1)
    print(f"=" * 60)
    print(f"AC-MPC Training")
    print(f"=" * 60)
    print(f"Case: {case}")
    print(f"Resume: {resume}")
    print(f"Start containers: {start_containers}")
    print(f"=" * 60)

    # Get case
    case_obj = get_case(case)
    config = case_obj.config
    device = config.device

    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"

    print(f"Device: {device}")

    # Start containers if requested
    if start_containers:
        start_docker_compose()

        # Wait for rosbridge
        if not wait_for_rosbridge(timeout=ROSBRIDGE_TIMEOUT):
            print("Failed to connect to rosbridge")
            stop_docker_compose()
            sys.exit(1)

    try:
        # Create experiment directory
        exp_dir = create_experiment_dir(case)
        print(f"Experiment directory: {exp_dir}")

        # Save config
        save_config(exp_dir, case_obj)

        # Create environment
        print("Creating environment...")
        env = make_env(case_obj)

        # Create trainer
        print("Creating trainer...")
        trainer = PPOTrainer.from_case(config, device=device)

        # Resume from checkpoint if requested
        if resume:
            print(f"Resuming from checkpoint: {resume}")
            checkpoint_path = Path(resume)
            if checkpoint_path.exists():
                trainer.load_checkpoint(checkpoint_path)
            else:
                print(f"Warning: Checkpoint not found at {resume}, starting fresh")

        # TensorBoard writer
        log_dir = exp_dir / "logs"
        writer = SummaryWriter(log_dir=str(log_dir))

        # Training loop
        max_epochs = config.max_epochs
        eval_freq = config.eval_freq
        save_freq = config.save_freq

        print(f"Starting training for {max_epochs} epochs...")
        print(f"Eval every {eval_freq} epochs, save every {save_freq} epochs")

        for epoch in range(max_epochs):
            # Collect rollouts
            rollout_metrics = trainer.collect_rollouts(env)

            # Train step
            train_metrics = trainer.train_step()

            # Log to TensorBoard
            global_step = trainer.global_step

            # Training metrics
            writer.add_scalar(
                "train/policy_loss", train_metrics["policy_loss"], global_step
            )
            writer.add_scalar(
                "train/value_loss", train_metrics["value_loss"], global_step
            )
            writer.add_scalar(
                "train/exploration_std", train_metrics["exploration_std"], global_step
            )
            writer.add_scalar(
                "train/clip_fraction", train_metrics["clip_fraction"], global_step
            )

            # Rollout metrics
            writer.add_scalar(
                "rollout/rollout_reward", rollout_metrics["rollout_reward"], global_step
            )
            writer.add_scalar(
                "rollout/episodes", rollout_metrics["episodes"], global_step
            )
            writer.add_scalar(
                "rollout/rollout_steps", rollout_metrics["rollout_steps"], global_step
            )

            # Console output - every epoch
            print(
                f"Epoch {epoch + 1}/{max_epochs} | "
                f"steps: {global_step} | "
                f"reward: {rollout_metrics['rollout_reward']:+.4f} | "
                f"policy: {train_metrics['policy_loss']:+.4f} | "
                f"value: {train_metrics['value_loss']:+.4f} | "
                f"std: {train_metrics['exploration_std']:.3f}"
            )

            # Evaluation
            if (epoch + 1) % eval_freq == 0:
                eval_metrics = trainer.evaluate()
                writer.add_scalar(
                    "eval/eval_reward", eval_metrics["eval_reward"], global_step
                )
                print(f"  → eval: {eval_metrics['eval_reward']:+.4f}")

            # Save checkpoint
            if (epoch + 1) % save_freq == 0:
                checkpoint_path = exp_dir / "checkpoints" / f"epoch_{epoch + 1}.pt"
                trainer.save_checkpoint(checkpoint_path)
                print(f"  → saved: {checkpoint_path.name}")

        # Save final checkpoint
        final_path = exp_dir / "checkpoints" / "final.pt"
        trainer.save_checkpoint(final_path)
        print(f"Final checkpoint saved: {final_path}")

        writer.close()
        print("Training complete!")

    except KeyboardInterrupt:
        print("\nTraining interrupted by user")
    except Exception as e:
        print(f"\nTraining error: {e}")
        raise
    finally:
        if start_containers:
            stop_docker_compose()


def main():
    """Main entry point."""
    tyro.cli(train)


if __name__ == "__main__":
    main()
