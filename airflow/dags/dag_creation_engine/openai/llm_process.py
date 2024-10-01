import os
import logging

import duckdb
import pandas as pd
from openai import OpenAI


logging.basicConfig(format="[%(levelname)s] %(asctime)s : %(message)s", level=logging.INFO, force=True)


def process_disease_info(*args, **kwargs):
    source_schema = kwargs["source_schema"]
    source_table = kwargs["source_table"]
    target_schema = kwargs["target_schema"]
    target_table = kwargs["target_table"]

    logging.info(f"processing disease info for table {source_schema}.{source_table}")

    db = duckdb.connect(os.getenv("DUCKDB_PATH"))
    df = db.sql(
        f"""select 
                condition_id, 
                condition_term_raw
                from {source_schema}.{source_table}
                """
    ).to_df()
    # TODO: add more flexibility to create other prompt types and other classifications

    df = standardize_diseases(df, column_name="condition_term_raw", standardized_col_name="condition_term_processed")

    logging.info(f"processed dataframe, starting duckdb insert into table {target_schema}.{target_table}")

    db.sql(f"CREATE SCHEMA IF NOT EXISTS {target_schema};")
    db.sql(f"CREATE OR REPLACE TABLE {target_schema}.{target_table} AS SELECT * FROM df")

    logging.info("Successfully inserted data")


def standardize_diseases(df, column_name, standardized_col_name):

    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
    )
    logging.info(f"starting OpenAI prompts")

    base_prompt = """I will give you a broad description of a disease. 
    I'd like to classify them so that similar diseases get classified under the same disease name.
    Example: input  Urogenital Diseases needs to yield the ICD standard for Urogenital Diseases.
    Here is the disease:"""
    standardized_terms = []
    input_list = df[column_name].to_list()
    fake_run = False

    logging.info(f"{len(input_list)} rows to process")

    for element in input_list:
        try:
            if fake_run:
                standardized_terms.append("fake classification for test purposes")
            else:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": """You are a medical doctor that classifies diseases following the international classification of diseases (ICD-11).
                                    You will only respond with a string element like 'Cardiovascular disease', and no additional chatting.""",
                        },
                        {"role": "user", "content": f"{base_prompt} {element}"},
                    ],
                )
                standardized_terms.append(response.choices[0].message.content.strip())

        except Exception as e:
            logging.info(f"Error processing term {element}: {str(e)}")
            standardized_terms.append(element)

    df[standardized_col_name] = standardized_terms
    return df
