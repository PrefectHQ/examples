from prefect import serve

from atproto_dashboard.assets import ingest_atproto_data
from atproto_dashboard.dbt_flow import transform_data
from atproto_dashboard.pipeline import run_pipeline


if __name__ == "__main__":
    # Create deployments

    # Full pipeline deployment (runs daily)
    pipeline_deployment = run_pipeline.to_deployment(
        name="atproto-dashboard-daily",
        cron="0 0 * * *",  # Daily at midnight
        tags=["pipeline", "daily"],
        description="Full ATProto dashboard pipeline - ingestion and transformation",
    )

    # Individual deployments for ad-hoc runs
    ingest_deployment = ingest_atproto_data.to_deployment(
        name="ingest-atproto",
        tags=["atproto", "ingestion"],
        description="Ingest ATProto data only",
    )

    transform_deployment = transform_data.to_deployment(
        name="transform-data",
        tags=["dbt", "transform"],
        description="Run dbt transformations only",
    )

    # Serve all deployments
    serve(pipeline_deployment, ingest_deployment, transform_deployment)
