// Declare that we need the Prefect provider
// NOTE: Fails when both PREFECT_CLOUD_ACCOUNT_ID and PREFECT_API_URL are set
terraform {
  required_providers {
    prefect = {
      source = "PrefectHQ/prefect"
    }
  }
}

// Create a workspace
locals {
  workspace_handle = replace(replace(lower(var.prefect_workspace_name), " ", "-"), "_", "-")
}

resource "prefect_workspace" "workspace" {
  name   = var.prefect_workspace_name
  handle = local.workspace_handle
}

// Create a service account and add it to the workspace
resource "prefect_service_account" "service_account" {
  name              = "prefect-worker"
  account_role_name = "Member"
  depends_on        = [prefect_workspace.workspace]
}

data "prefect_workspace_role" "worker" {
  name       = "Worker"
  depends_on = [prefect_workspace.workspace]
}

resource "prefect_workspace_access" "workspace_access" {
  accessor_type     = "SERVICE_ACCOUNT"
  accessor_id       = prefect_service_account.service_account.id
  workspace_id      = prefect_workspace.workspace.id
  workspace_role_id = data.prefect_workspace_role.worker.id
}

// Create basic process and docker work pools
resource "prefect_work_pool" "process_work_pool" {
  name         = "process"
  type         = "process"
  workspace_id = prefect_workspace.workspace.id
}

resource "prefect_work_pool" "docker_work_pool" {
  name         = "docker"
  type         = "docker"
  workspace_id = prefect_workspace.workspace.id
}

