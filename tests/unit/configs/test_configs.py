"""Unit tests for configuration schemas."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from acmpc.cases.configs import (
    ACMPCConfig,
    CaseConfig,
    CostMapConfig,
    EnvConfig,
    MPCConfig,
    PPOConfig,
    ValueNetworkConfig,
)
from acmpc.registries.robots import (
    RobotParams,
    RobotParamsRegistry,
    get_robot_params,
)


class TestPPOConfig:
    def test_default_values(self):
        config = PPOConfig()
        assert config.learning_rate == 3e-4
        assert config.n_steps == 2048
        assert config.batch_size == 64
        assert config.n_epochs == 10
        assert config.gamma == 0.99
        assert config.gae_lambda == 0.95
        assert config.clip_range == 0.2
        assert config.ent_coef == 0.01
        assert config.vf_coef == 0.5
        assert config.max_grad_norm == 0.5

    def test_custom_values(self):
        config = PPOConfig(
            learning_rate=1e-3,
            n_steps=1024,
            batch_size=32,
        )
        assert config.learning_rate == 1e-3
        assert config.n_steps == 1024
        assert config.batch_size == 32

    def test_invalid_learning_rate(self):
        with pytest.raises(ValidationError):
            PPOConfig(learning_rate=-1e-3)

    def test_invalid_gamma(self):
        with pytest.raises(ValidationError):
            PPOConfig(gamma=1.5)

    def test_serialization(self):
        config = PPOConfig()
        data = config.model_dump()
        assert isinstance(data, dict)
        assert "learning_rate" in data

    def test_json_serialization(self):
        config = PPOConfig()
        json_str = config.model_dump_json()
        loaded = PPOConfig.model_validate_json(json_str)
        assert loaded.learning_rate == config.learning_rate


class TestCostMapConfig:
    def test_default_values(self):
        config = CostMapConfig()
        assert config.matrix_type == "diagonal"
        assert config.hidden_layers == [128, 128]
        assert config.activation == "relu"

    def test_custom_values(self):
        config = CostMapConfig(
            matrix_type="cholesky",
            hidden_layers=[256, 256, 128],
            activation="tanh",
        )
        assert config.matrix_type == "cholesky"
        assert config.hidden_layers == [256, 256, 128]
        assert config.activation == "tanh"

    def test_invalid_matrix_type(self):
        with pytest.raises(ValidationError):
            CostMapConfig(matrix_type="invalid")


class TestMPCConfig:
    def test_default_values(self):
        config = MPCConfig()
        assert config.horizon == 15
        assert config.solver_type == "osqp"

    def test_custom_values(self):
        config = MPCConfig(horizon=20, solver_type="qp")
        assert config.horizon == 20
        assert config.solver_type == "qp"

    def test_invalid_horizon(self):
        with pytest.raises(ValidationError):
            MPCConfig(horizon=0)

    def test_invalid_horizon_exceeds_limit(self):
        with pytest.raises(ValidationError):
            MPCConfig(horizon=101)


class TestValueNetworkConfig:
    def test_default_values(self):
        config = ValueNetworkConfig()
        assert config.hidden_layers == [128, 128]
        assert config.activation == "relu"

    def test_custom_values(self):
        config = ValueNetworkConfig(
            hidden_layers=[256, 256, 128],
            activation="tanh",
        )
        assert config.hidden_layers == [256, 256, 128]
        assert config.activation == "tanh"


class TestACMPCConfig:
    def test_default_values(self):
        config = ACMPCConfig()
        assert isinstance(config.cost_map, CostMapConfig)
        assert config.cost_map.matrix_type == "diagonal"
        assert config.cost_map.hidden_layers == [128, 128]
        assert config.cost_map.activation == "relu"
        assert isinstance(config.mpc, MPCConfig)
        assert config.mpc.horizon == 15
        assert config.mpc.solver_type == "osqp"
        assert isinstance(config.value_network, ValueNetworkConfig)
        assert config.value_network.hidden_layers == [128, 128]
        assert config.value_network.activation == "relu"

    def test_custom_values(self):
        config = ACMPCConfig(
            cost_map=CostMapConfig(
                matrix_type="cholesky",
                hidden_layers=[256, 256, 128],
            ),
            mpc=MPCConfig(horizon=20),
        )
        assert config.cost_map.matrix_type == "cholesky"
        assert config.cost_map.hidden_layers == [256, 256, 128]
        assert config.mpc.horizon == 20

    def test_nested_config_override(self):
        config = ACMPCConfig(
            cost_map=CostMapConfig(matrix_type="full"),
            mpc=MPCConfig(horizon=10, solver_type="qp"),
            value_network=ValueNetworkConfig(hidden_layers=[64, 64]),
        )
        assert config.cost_map.matrix_type == "full"
        assert config.mpc.horizon == 10
        assert config.mpc.solver_type == "qp"
        assert config.value_network.hidden_layers == [64, 64]

    def test_serialization(self):
        config = ACMPCConfig()
        data = config.model_dump()
        assert isinstance(data, dict)
        assert "cost_map" in data
        assert "mpc" in data
        assert "value_network" in data


class TestEnvConfig:
    def test_default_values(self):
        config = EnvConfig()
        assert config.world_name == "turtlebot3_empty"
        assert config.reward_fn == "dense_goal"
        assert config.goal_threshold == 0.3
        assert config.goal_min_distance == 1.0
        assert config.goal_max_distance == 3.0
        assert config.max_steps == 500
        assert config.dt == 0.1

    def test_custom_values(self):
        config = EnvConfig(
            reward_fn="dense_goal",
            max_steps=1000,
        )
        assert config.world_name == "turtlebot3_empty"
        assert config.reward_fn == "dense_goal"
        assert config.max_steps == 1000

    def test_invalid_dt(self):
        with pytest.raises(ValidationError):
            EnvConfig(dt=-0.1)

    def test_invalid_goal_threshold(self):
        with pytest.raises(ValidationError):
            EnvConfig(goal_threshold=0.0)

    def test_invalid_reward_fn(self):
        with pytest.raises(ValidationError):
            EnvConfig(reward_fn="nonexistent_reward")


class TestRobotParams:
    def test_burger_params(self):
        params = RobotParamsRegistry.get("burger")
        assert params.name == "TurtleBot3 Burger"
        assert params.max_linear_vel == 0.22
        assert params.max_angular_vel == 2.84
        assert params.wheel_radius == 0.033
        assert params.wheel_base == 0.16

    def test_waffle_params(self):
        params = RobotParamsRegistry.get("waffle")
        assert params.name == "TurtleBot3 Waffle"
        assert params.max_linear_vel == 0.26

    def test_waffle_pi_params(self):
        params = RobotParamsRegistry.get("waffle_pi")
        assert params.name == "TurtleBot3 Waffle Pi"
        assert params.max_linear_vel == 0.18

    def test_get_robot_params_valid(self):
        params = get_robot_params("burger")
        assert params.name == "TurtleBot3 Burger"

    def test_get_robot_params_invalid(self):
        with pytest.raises(KeyError):
            get_robot_params("invalid_robot")

    def test_invalid_wheel_radius(self):
        with pytest.raises(ValueError):
            RobotParams(
                name="test",
                max_linear_vel=0.22,
                max_angular_vel=2.84,
                max_linear_acc=1.0,
                max_angular_acc=4.0,
                wheel_radius=-0.033,
                wheel_base=0.16,
                lidar_range=3.5,
                lidar_rays=360,
                lidar_fov=6.28,
            )


class TestCaseConfig:
    def test_default_values(self):
        config = CaseConfig(name="test_case")
        assert config.name == "test_case"
        assert config.description == ""
        assert config.env.robot_name == "burger"
        assert config.device == "auto"
        assert config.seed == 42
        assert isinstance(config.env, EnvConfig)
        assert isinstance(config.acmpc, ACMPCConfig)
        assert isinstance(config.ppo, PPOConfig)
        assert config.max_epochs == 1000
        assert config.eval_freq == 10
        assert config.save_freq == 50

    def test_custom_values(self):
        config = CaseConfig(
            name="nav_test",
            description="Navigation test case",
            env=EnvConfig(robot_name="waffle"),
            device="cuda",
            seed=123,
            max_epochs=500,
            eval_freq=5,
        )
        assert config.name == "nav_test"
        assert config.description == "Navigation test case"
        assert config.env.robot_name == "waffle"
        assert config.device == "cuda"
        assert config.seed == 123
        assert config.max_epochs == 500
        assert config.eval_freq == 5

    def test_invalid_robot_name(self):
        with pytest.raises(ValidationError):
            CaseConfig(name="test", env=EnvConfig(robot_name="invalid"))

    def test_serialization(self):
        config = CaseConfig(name="test_case", env=EnvConfig(robot_name="burger"))
        data = config.model_dump()
        assert isinstance(data, dict)
        assert data["name"] == "test_case"
        assert data["env"]["robot_name"] == "burger"

    def test_json_serialization(self):
        config = CaseConfig(name="test_case", env=EnvConfig(robot_name="burger"))
        json_str = config.model_dump_json()
        loaded = CaseConfig.model_validate_json(json_str)
        assert loaded.name == config.name
        assert loaded.env.robot_name == config.env.robot_name

    def test_nested_config_override(self):
        config = CaseConfig(
            name="test",
            ppo=PPOConfig(learning_rate=1e-3),
            acmpc=ACMPCConfig(mpc=MPCConfig(horizon=20)),
        )
        assert config.ppo.learning_rate == 1e-3
        assert config.acmpc.mpc.horizon == 20


class TestCase:
    def test_case_creation(self):
        from acmpc.cases import Case
        from acmpc.cases.configs import CaseConfig, EnvConfig

        case = Case(
            name="test_case",
            description="Test case",
            config=CaseConfig(
                name="test_case",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        assert case.name == "test_case"
        assert case.description == "Test case"
        assert case.config.env.robot_name == "burger"

    def test_case_validation_invalid_reward(self):
        from acmpc.cases.configs import CaseConfig, EnvConfig

        with pytest.raises(ValidationError):
            CaseConfig(
                name="test_case",
                env=EnvConfig(robot_name="burger", reward_fn="invalid_reward"),
            )

    def test_case_validation_invalid_robot(self):
        from acmpc.cases.configs import CaseConfig, EnvConfig

        with pytest.raises(ValidationError):
            CaseConfig(
                name="test_case",
                env=EnvConfig(robot_name="invalid_robot", reward_fn="dense_goal"),
            )

    def test_get_reward_fn(self):
        from acmpc.cases import Case, CaseRegistryInstance
        from acmpc.cases.configs import CaseConfig, EnvConfig

        test_case = Case(
            name="test_reward_fn",
            config=CaseConfig(
                name="test_reward_fn",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        CaseRegistryInstance.register("test_reward_fn", test_case)

        reward_fn = test_case.reward_fn
        assert callable(reward_fn)

    def test_get_robot_params(self):
        from acmpc.cases import Case, CaseRegistryInstance
        from acmpc.cases.configs import CaseConfig, EnvConfig

        test_case = Case(
            name="test_robot_params",
            config=CaseConfig(
                name="test_robot_params",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        CaseRegistryInstance.register("test_robot_params", test_case)

        robot_params = test_case.robot_params
        assert robot_params.name == "TurtleBot3 Burger"

    def test_case_registry_register(self):
        from acmpc.cases import Case, CaseRegistryInstance
        from acmpc.cases.configs import CaseConfig, EnvConfig

        test_case = Case(
            name="test_register",
            config=CaseConfig(
                name="test_register",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        CaseRegistryInstance.register("test_register", test_case)
        assert "test_register" in CaseRegistryInstance

    def test_case_registry_get(self):
        from acmpc.cases import Case, CaseRegistryInstance
        from acmpc.cases.configs import CaseConfig, EnvConfig

        test_case = Case(
            name="test_get",
            config=CaseConfig(
                name="test_get",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        CaseRegistryInstance.register("test_get", test_case)

        retrieved = CaseRegistryInstance.get("test_get")
        assert retrieved.name == "test_get"

    def test_case_registry_get_config(self):
        from acmpc.cases import Case, CaseRegistryInstance
        from acmpc.cases.configs import CaseConfig, EnvConfig

        test_case = Case(
            name="test_config",
            config=CaseConfig(
                name="test_config",
                env=EnvConfig(robot_name="burger", reward_fn="dense_goal"),
            ),
        )
        CaseRegistryInstance.register("test_config", test_case)

        config = CaseRegistryInstance.get_config("test_config")
        assert isinstance(config, CaseConfig)
        assert config.env.robot_name == "burger"

    def test_case_registry_list_cases(self):
        from acmpc.cases import list_cases

        cases = list_cases()
        assert isinstance(cases, list)
