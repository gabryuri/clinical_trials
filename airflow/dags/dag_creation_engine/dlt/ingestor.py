from typing import Any
import logging
import os

import yaml
import duckdb
import dlt
from dlt.sources.rest_api import (
    RESTAPIConfig,
    rest_api_resources,
)

logger = logging.getLogger(__name__)


@dlt.source()
def clinical_trials(params="{'query.cond': 'COVID'}"):
    logger.info(f"DLT source with parameters {params}")
    cfg_dict = {
        "client": {"base_url": "https://clinicaltrials.gov/api/v2"},
        "resource_defaults": {
            "primary_key": "protocol_section__identification_module__nct_id",
            "write_disposition": "append",
            "endpoint": {
                "params": {
                    "pageSize": 1000,
                },
                "paginator": {"type": "single_page"},
                # Commenting this out - for conveniency we will just load one page and use append instead of merge
                # "paginator": {
                #     "type": "cursor",
                #     "cursor_path": "nextPageToken",
                #     "cursor_param": "pageToken",
                #     },
            },
        },
        "resources": [
            {
                "name": "studies",
                "endpoint": {"path": "studies", "params": yaml.safe_load(params)},
            }
        ],
    }
    logger.info(f"complete rest config: \n {cfg_dict}")
    config: RESTAPIConfig = cfg_dict

    yield from rest_api_resources(config)


def load_clinical_trials(*args, **kwargs):
    logger.info(f"load_clinical_trials called with kwargs {kwargs}")
    db = duckdb.connect(os.getenv("DUCKDB_PATH"))
    pipeline = dlt.pipeline(
        pipeline_name="load_clinical_trials",
        destination=dlt.destinations.duckdb(db),
        dataset_name="clinical_trials",
    )

    logger.info("Starting DLT load")
    load_info = pipeline.run(clinical_trials(kwargs["params"]))
    logger.info(f"DLT load info {load_info}")


if __name__ == "__main__":
    db = duckdb.connect(os.getenv("DUCKDB_PATH"))
    load_clinical_trials("{'query.cond': 'COVID19'}")
