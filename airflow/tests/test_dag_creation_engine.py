import pytest
from unittest.mock import Mock
import unittest
from airflow.models import DagBag
import os
import sys
import yaml
from datetime import datetime
from tests.utils import build_test_base_path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
print(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dags")))

os.environ["KUBERNETES_CLUSTER"] = "test-cluster"
os.environ["ENV"] = "dev"

from dags.dag_creation_engine.dag_factory import create_dag


class TestDagCreationEngine(unittest.TestCase):
    def test_valid_complete_dag_loaded_upstreams(self):
        with open(f"{build_test_base_path()}/fixtures/valid_complete_arguments_dag.yaml") as f:
            dag_yaml = yaml.safe_load(f)
            print(dag_yaml)
            dag = create_dag(
                logging=Mock(),
                dag_id="test_dag_id",
                schedule_interval=dag_yaml["schedule_interval"],
                start_date=datetime.strptime(dag_yaml["start_date"], "%Y-%m-%d"),
                task_configs=dag_yaml["groups"],
            )

        assert dag is not None
        assert len(dag.tasks) == 6
        assert dag.get_task("respiratory-conditions.clinical-trials-gov-influenza").upstream_task_ids == set()
        assert dag.get_task("transformation.clinical-trials-gov-dbt").upstream_task_ids == {
            "respiratory-conditions.clinical-trials-gov-influenza",
            "respiratory-conditions.clinical-trials-gov-covid",
            "endocrinal-conditions.clinical-trials-gov-diabetes",
            "endocrinal-conditions.clinical-trials-gov-menopause",
        }

    def test_valid_complete_dag_task_definitions(self):
        with open(f"{build_test_base_path()}/fixtures/valid_complete_arguments_dag.yaml") as f:
            dag_yaml = yaml.safe_load(f)
            print(dag_yaml)
            dag = create_dag(
                logging=Mock(),
                dag_id="test_dag_id",
                schedule_interval=dag_yaml["schedule_interval"],
                start_date=datetime.strptime(dag_yaml["start_date"], "%Y-%m-%d"),
                task_configs=dag_yaml["groups"],
            )

        assert dag.get_task("respiratory-conditions.clinical-trials-gov-influenza").task_type == "PythonOperator"
        assert dag.get_task("respiratory-conditions.clinical-trials-gov-influenza").op_kwargs == {
            "params": "{'query.cond': 'INFLUENZA'}",
            "pipeline": "respiratory-conditions",
        }

        assert dag.get_task("respiratory-conditions.clinical-trials-gov-covid").task_type == "PythonOperator"
        assert dag.get_task("respiratory-conditions.clinical-trials-gov-covid").op_kwargs == {
            "params": "{'query.cond': 'COVID'}",
            "pipeline": "respiratory-conditions",
        }

        assert dag.get_task("transformation.clinical-trials-gov-dbt").task_type == "BashOperator"

        assert (
            dag.get_task("transformation.clinical-trials-gov-openai-standardize-conditions").task_type
            == "PythonOperator"
        )
        assert dag.get_task("transformation.clinical-trials-gov-openai-standardize-conditions").op_kwargs == {
            "source_schema": "clinical_trials_preprocessed",
            "source_table": "dim_conditions",
            "target_schema": "clinical_trials_processed",
            "target_table": "dim_conditions_processed",
        }
