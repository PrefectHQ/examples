variable "source_workspace" {
  type        = string
  description = "The source workspace to replicate events from"
}

variable "target_workspace" {
  type        = string
  description = "The target workspace to replicate events to"
}

variable "events" {
  type        = list(string)
  description = "The events to replicate"
  default     = ["prefect.flow-run.Completed"]
}
