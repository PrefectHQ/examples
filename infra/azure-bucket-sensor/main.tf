// WARNING: This script is not yet tested! Here be dragons!

// Define the providers
terraform {
  required_providers {
    azurerm = {
      source = "hashicorp/azurerm"
    }
    prefect = {
      source = "prefecthq/prefect"
    }
  }
}

provider "azurerm" {}

provider "prefect" {
  account_id = var.prefect_account_id
}

// Prefect Resources
// Service Account + Webhook
data "prefect_workspace" "workspace" {
  id = var.prefect_workspace_id
}

resource "prefect_service_account" "service_account" {
  name              = "azure-bucket-sensor"
  account_role_name = "Member"
}

data "prefect_workspace_role" "developer" {
  name = "Developer"
}

resource "prefect_workspace_access" "workspace_access" {
  accessor_type     = "SERVICE_ACCOUNT"
  accessor_id       = prefect_service_account.service_account.id
  workspace_id      = data.prefect_workspace.workspace.id
  workspace_role_id = data.prefect_workspace_role.developer.id
}

resource "prefect_webhook" "target_webhook" {
  name        = "azure-bucket-sensor"
  description = "Receives events from Azure Storage Blob"
  enabled     = true
  template = jsonencode({
    event = "azure.storage.blob.created"
    resource = {
      "prefect.resource.id"   = "azure.storage.${var.storage_account_name}"
      "prefect.resource.name" = "Azure Storage Blob"
    }
    // https://docs.prefect.io/v3/automate/events/webhook-triggers#accepting-cloudevents
    data = "{{ body|from_cloud_event(headers) }}"

  })
  service_account_id = prefect_service_account.service_account.id
  workspace_id       = data.prefect_workspace.workspace.id
}

// Azure Resources
// Storage Account + Event Grid
resource "azurerm_storage_account" "storage_account" {
  name                     = var.storage_account_name
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
}

resource "azurerm_eventgrid_system_topic" "system_topic" {
  name                   = "azure-bucket-sensor"
  resource_group_name    = var.resource_group_name
  location               = var.location
  source_arm_resource_id = azurerm_storage_account.storage_account.id
  topic_type             = "Microsoft.Storage.StorageAccounts"
}

resource "azurerm_eventgrid_event_subscription" "event_subscription" {
  name  = "azure-bucket-sensor"
  scope = azurerm_eventgrid_system_topic.system_topic.id

  webhook_endpoint {
    url = prefect_webhook.target_webhook.endpoint
  }

  retry_policy {
    max_delivery_attempts = 5
    event_time_to_live    = 1440
  }

  advanced_filter {
    string_in {
      key    = "Data.eventType"
      values = ["Microsoft.Storage.BlobCreated"]
    }
  }
}
