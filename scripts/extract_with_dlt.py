# /// script
# dependencies = ["prefect", "dlt"]
# ///

import dlt
from dlt.sources.rest_api import rest_api_source
from prefect.settings import PREFECT_API_KEY, PREFECT_API_URL


source = rest_api_source(
    {
        "client": {
            "base_url": PREFECT_API_URL.value(),
            "auth": {
                "type": "bearer",
                "token": PREFECT_API_KEY.value(),
            },
            "paginator": {
                "type": "page_number",
                "total_path": "pages",
                "base_page": 1,
            },
        },
        "resource_defaults": {
            "endpoint": {
                "method": "POST",
                "data_selector": "results",
            },
            "primary_key": "id",
            "write_disposition": "merge",
        },
        "resources": [
            {
                "name": name,
                "endpoint": {
                    "path": f"{name}/paginate",
                },
            }
            for name in ["deployments", "flows", "flow_runs"]
        ],
    }
)

pipeline = dlt.pipeline(
    pipeline_name="prefect-cloud",
    destination="duckdb",
    dataset_name="prefect-cloud",
    progress="log",
)


if __name__ == "__main__":
    load_info = pipeline.run(source)
    print(load_info)
