output "prefect_workspace_id" {
  value = prefect_workspace.workspace.id
}

output "prefect_service_account_api_key" {
  value     = prefect_service_account.service_account.api_key
  sensitive = true
}
