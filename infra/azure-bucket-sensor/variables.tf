variable "prefect_account_id" {
  type        = string
  description = "The ID of the Prefect account that will host the webhook"
}

variable "prefect_workspace_id" {
  type        = string
  description = "The ID of the Prefect workspace that will host the webhook"
}

variable "storage_account_name" {
  type        = string
  description = "The name of the Azure Storage Account"
}

variable "resource_group_name" {
  type        = string
  description = "The name of the Azure Resource Group"
}

variable "location" {
  type        = string
  description = "The Azure region to deploy the resources"
}
