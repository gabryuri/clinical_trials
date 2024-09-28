import unittest
import pytest
import os
from scripts.validator.validate_dags import validate_yaml, DAGConsistencyException, DAGCyclicDependencyException
from jsonschema.exceptions import ValidationError
from tests.utils import build_test_base_path


class TestDAGValidator(unittest.TestCase):
    def setUp(self):
        self.dag_schema_path = "scripts/validator/dag_schema.json"
        self.task_schema_path = "scripts/validator/task_schemas.json"

    def test_valid_minimal_arguments_dag(self):
        validate_yaml(
            f"{build_test_base_path()}/fixtures/valid_minimal_arguments_dag.yaml",
            self.dag_schema_path,
            self.task_schema_path,
        )

    def test_valid_complete_arguments_dag(self):
        validate_yaml(
            f"{build_test_base_path()}/fixtures/valid_complete_arguments_dag.yaml",
            self.dag_schema_path,
            self.task_schema_path,
        )

    def test_invalid_cyclic_dag(self):
        errors = validate_yaml(
            f"{build_test_base_path()}/fixtures/invalid_cyclic_dag.yaml",
            self.dag_schema_path,
            self.task_schema_path,
        )
        assert errors == ["Cyclic dependency detected in DAG invalid_cyclic_dag.yaml."]

    def test_invalid_broken_dependency_dag(self):
        errors = validate_yaml(
            f"{build_test_base_path()}/fixtures/invalid_broken_dependency_dag.yaml",
            self.dag_schema_path,
            self.task_schema_path,
        )
        assert errors == ["Task 'clinical-trials-gov-covid' has an invalid dependency: 'non-existent-task'"]


if __name__ == "__main__":
    unittest.main()
