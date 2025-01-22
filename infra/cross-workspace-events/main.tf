terraform {
  required_providers {
    prefect = {
      source = "prefecthq/prefect"
    }
  }
}

data "prefect_workspace" "source" {
  id = var.source_workspace
}

data "prefect_workspace" "target" {
  id = var.target_workspace
}

// Create a service account to use for webhook authentication
resource "prefect_service_account" "service_account" {
  name              = "cross-workspace-events"
  account_role_name = "Member"
}

data "prefect_workspace_role" "developer" {
  name = "Developer"
}

resource "prefect_workspace_access" "source_access" {
  accessor_type     = "SERVICE_ACCOUNT"
  accessor_id       = prefect_service_account.service_account.id
  workspace_id      = data.prefect_workspace.source.id
  workspace_role_id = data.prefect_workspace_role.developer.id
}

resource "prefect_workspace_access" "target_access" {
  accessor_type     = "SERVICE_ACCOUNT"
  accessor_id       = prefect_service_account.service_account.id
  workspace_id      = data.prefect_workspace.target.id
  workspace_role_id = data.prefect_workspace_role.developer.id
}

// Create the webhook that will receive events from the source workspace
resource "prefect_webhook" "target_webhook" {
  name        = "cross-workspace-events-target"
  description = "Receive events from the ${data.prefect_workspace.source.name} workspace"
  enabled     = true
  template = jsonencode({
    event = "prefect.cross-workspace-event.received"
    resource = {
      "prefect.resource.id"   = "prefect.event"
      "prefect.resource.name" = "Prefect Cross-Workspace Event"
    }
    data = "{{ body }}"
  })

  service_account_id = prefect_service_account.service_account.id
  workspace_id       = data.prefect_workspace.target.id
}

resource "prefect_block" "source_webhook_block" {
  name      = "cross-workspace-events-source"
  type_slug = "webhook"

  data = jsonencode({
    "url" = prefect_webhook.target_webhook.endpoint
    "headers" = {
      "Authorization" = "Bearer ${prefect_service_account.service_account.api_key}"
    }
  })

  workspace_id = data.prefect_workspace.source.id
}

resource "prefect_automation" "source_automation" {
  name        = "cross-workspace-events-source"
  description = "Send events to the ${data.prefect_workspace.target.name} workspace"
  enabled     = true

  trigger = {
    event = {
      posture = "Reactive"
      match = jsonencode({
        "prefect.resource.id" : "prefect.flow-run.*"
      })
      expect    = var.events
      for_each  = ["prefect.resource.id"]
      threshold = 1
      within    = 0
    }
  }
  actions = [
    {
      type              = "call-webhook"
      block_document_id = prefect_block.source_webhook_block.id
      body = jsonencode({
        "event" = "{{ event }}"
      })
    }
  ]
}