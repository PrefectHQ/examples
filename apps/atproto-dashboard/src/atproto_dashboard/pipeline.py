"""
Main pipeline that orchestrates the entire ATProto dashboard workflow.
"""

from prefect import flow

from atproto_dashboard.assets import ingest_atproto_data
from atproto_dashboard.dbt_flow import transform_data


@flow(name="atproto-dashboard-pipeline")
def run_pipeline(
    starter_pack_uri: str = "at://did:plc:xbtmt2zjwlrfegqvch7fboei/app.bsky.graph.starterpack/3le4a5obum62l",
) -> dict:
    """
    Main pipeline that orchestrates:
    1. Ingestion of ATProto data (creates assets)
    2. Transformation with dbt (creates derived assets)

    The assets created by this pipeline can be used by downstream consumers.
    """
    # Step 1: Ingest data from ATProto
    ingestion_result = ingest_atproto_data(starter_pack_uri)

    # Step 2: Transform data with dbt
    transform_result = transform_data()

    # Return combined results
    return {
        "ingestion": ingestion_result,
        "transformation": transform_result,
    }


if __name__ == "__main__":
    # Run the full pipeline
    result = run_pipeline()
    print(f"\nPipeline completed: {result}")
