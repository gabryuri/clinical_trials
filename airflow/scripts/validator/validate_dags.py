import os
import argparse
import yaml
import json
import jsonschema
import logging
from jsonschema import validate
from glob import glob

DAGS_DIR = "/".join([os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "dags"])


class DAGConsistencyException(Exception):
    """Exception raised for errors in DAG consistency."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class DAGCyclicDependencyException(Exception):
    """Exception raised when DAG has cyclic dependencies."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


logging.basicConfig(
    format="[%(levelname)s][%(asctime)s][%(filename)-15s][%(lineno)4d] - %(message)s",
    level=logging.INFO,
    force=True,
)
logger = logging.getLogger()


def is_cyclic_util(task_id, adjacency_list, visited, rec_stack):
    visited.add(task_id)
    rec_stack.add(task_id)

    for neighbor in adjacency_list.get(task_id, []):
        if neighbor not in visited:
            if is_cyclic_util(neighbor, adjacency_list, visited, rec_stack):
                return True
        elif neighbor in rec_stack:
            return True

    rec_stack.remove(task_id)
    return False


def is_cyclic(dag_config):
    adjacency_list = {}
    for task_group in dag_config["groups"]:
        for task_cfg in dag_config["groups"].get(task_group):
            task_id = task_cfg["task_id"]
            adjacency_list[task_id] = task_cfg.get("dependencies", [])

    # adjacency_list = {task["task_id"]: task.get("dependencies", []) for task in dag_config["tasks"]}
    visited = set()
    rec_stack = set()

    for task_id in adjacency_list:
        if task_id not in visited:
            if is_cyclic_util(task_id, adjacency_list, visited, rec_stack):
                return True
    return False


def load_schema(schema_file_path):
    # logger.info(f"loading schemas from {schema_file_path}")
    with open(schema_file_path, "r") as schema_file:
        return json.load(schema_file)


def validate_task(task, task_schemas):
    kind = task.get("kind")
    if kind not in task_schemas:
        raise ValueError(f"Unsupported task kind: {kind}")
    validate(instance=task, schema=task_schemas[kind])


def validate_yaml(yaml_file_path, dag_schema_path, task_schema_path):
    dag_schema = load_schema(dag_schema_path)
    task_schemas = load_schema(task_schema_path)
    dag_name = os.path.basename(yaml_file_path)
    file_errors = []

    try:
        # logger.info(f"Validating file {yaml_file_path}")
        with open(yaml_file_path, "r") as file:
            yaml_data = yaml.safe_load(file)

        validate(instance=yaml_data, schema=dag_schema)
        file_errors.extend(validate_dag_dependencies(dag_config=yaml_data, dag_name=dag_name))

        # logger.info(f"Dependencies and schema validated for {dag_name}, now validating tasks")
        for task in yaml_data.get("tasks", []):
            try:
                validate_task(task, task_schemas)
            except (jsonschema.exceptions.ValidationError, ValueError) as e:
                file_errors.append(f"Error in task '{task.get('task_id', 'unknown')}': {str(e)}")

    except jsonschema.exceptions.ValidationError as e:
        file_errors.append(f"Schema validation error in {dag_name}: {str(e)}")

    return file_errors


def validate_dag_dependencies(dag_config, dag_name):
    errors = []
    if is_cyclic(dag_config):
        errors.append(f"Cyclic dependency detected in DAG {dag_name}.")

    # task_ids = {task["task_id"] for task in dag_config["groups"]}
    task_ids = []
    for task_group in dag_config["groups"]:
        task_ids.extend([task_cfg["task_id"] for task_cfg in dag_config["groups"].get(task_group)])

    for group in dag_config["groups"]:
        for task in dag_config["groups"].get(group):
            for dependency in task.get("dependencies", []):
                if dependency not in task_ids:
                    errors.append(f"Task '{task['task_id']}' has an invalid dependency: '{dependency.strip()}'")

    return errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate YAML files against schemas.")
    parser.add_argument(
        "-yaml_file", dest="yaml_file", help="Optional path to a specific YAML file to be validated.", default=None
    )
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    dag_schema_path = os.path.join(script_dir, "dag_schema.json")
    task_schema_path = os.path.join(script_dir, "task_schemas.json")

    error_dict = {}
    if args.yaml_file:
        yaml_path = os.path.join(DAGS_DIR, args.yaml_file)
        error_dict[args.yaml_file] = validate_yaml(yaml_path, dag_schema_path, task_schema_path)
        # all_errors.extend(validate_yaml(yaml_path, dag_schema_path, task_schema_path))
    else:
        for yaml_file in glob(os.path.join(DAGS_DIR, "*.yaml")):
            file_errors = validate_yaml(yaml_file, dag_schema_path, task_schema_path)
            if file_errors:
                error_dict[os.path.basename(yaml_file)] = file_errors

    if error_dict:
        formatted_output = ""
        for filename, errors in error_dict.items():
            formatted_output += f"Errors in {filename}:\n"
            for error in errors:
                formatted_output += f"     - {error}\n"
        raise Exception(f"\n-----------VALIDATION FAILED-----------\n\n{formatted_output}")
