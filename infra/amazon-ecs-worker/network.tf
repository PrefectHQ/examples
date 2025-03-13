resource "aws_security_group" "prefect_worker" {
  name        = "prefect-worker-sg-${var.name}"
  description = "ECS Prefect worker"
  vpc_id      = var.vpc_id
}

resource "aws_security_group_rule" "network_outbound" {
  // S3 Gateway interfaces are implemented at the routing level which means we
  // can avoid the metered billing of a VPC endpoint interface by allowing
  // outbound traffic to the public IP ranges, which will be routed through
  // the Gateway interface:
  // https://docs.aws.amazon.com/AmazonS3/latest/userguide/privatelink-interface-endpoints.html
  description       = "Security group rule for Prefect Server running in Fargate."
  type              = "egress"
  security_group_id = aws_security_group.prefect_worker.id
  from_port         = 0
  to_port           = 0
  protocol          = "all"
  cidr_blocks       = ["0.0.0.0/0"]
}
