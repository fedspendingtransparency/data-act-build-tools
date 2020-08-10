provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {}
}

resource "aws_autoscaling_group" "api_asg" {
  name                      = "${var.api_name_prefix} (${var.aws_amis[var.aws_region]})"
  max_size                  = var.api_asg_max
  min_size                  = var.api_asg_min
  desired_capacity          = var.api_asg_desired
  min_elb_capacity          = var.api_asg_min
  health_check_type         = "ELB"
  health_check_grace_period = 30
  launch_configuration      = aws_launch_configuration.api_lc.name
  load_balancers            = var.api_elb_names
  target_group_arns         = var.api_target_group_arns
  vpc_zone_identifier       = split(",", var.subnets)

  tags = [
    {
      key                   = "Name"
      value                 = "${var.api_name_prefix} (${var.aws_amis[var.aws_region]})"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Application"
      value                 = "USAspending"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Component"
      value                 = "API"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Environment"
      value                 =  var.env_tag
      propagate_at_launch   = "true"
    },
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# When autoscaling decides to terminate an instance, instead of terminating it immediately, it will defer to the termination hook
# and place the instance into a Termination:Wait state for the specified heartbeat_timeout of 600 seconds (10 minutes).
# By that time, if the hook has not received a continue request, it will proceed with the default_result,
# in this case CONTINUE to terminate the instance.
# AWS Reference: https://docs.aws.amazon.com/autoscaling/ec2/userguide/lifecycle-hooks.html#preparing-for-notification
resource "aws_autoscaling_lifecycle_hook" "api_hook_termination" {
  name                    = "${var.api_name_prefix}-${var.aws_amis[var.aws_region]}"
  autoscaling_group_name  = aws_autoscaling_group.api_asg.name
  default_result          = "CONTINUE"
  heartbeat_timeout       = 600
  lifecycle_transition    = "autoscaling:EC2_INSTANCE_TERMINATING"
}

resource "aws_launch_configuration" "api_lc" {
  name                 = "${var.api_name_prefix} (${var.aws_amis[var.aws_region]})"
  image_id             = var.aws_amis[var.aws_region]
  instance_type        = var.api_instance_type
  iam_instance_profile = var.iam_profile
  security_groups      = split(",", var.sec_groups)
  user_data            = file("usaspending-start-staging.sh")
  key_name             = var.key_name
  ebs_optimized        = true
  lifecycle {
    create_before_destroy = true
  }
  root_block_device {
    volume_size = var.api_ebs_size
    volume_type = var.api_ebs_type
  }
}

resource "aws_autoscaling_policy" "api_scale_up" {
  name                   = "${var.api_name_prefix}_scaleup (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 600
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.api_asg.name
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_high_requests" {
  alarm_name          = "${var.api_name_prefix}_requestshigh (${var.aws_amis[var.aws_region]})"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  threshold           = "10000"

  metric_query {
    id          = "e1"
    expression  = "m1/m2"
    label       = "Requests Per Host"
    return_data = "true"
  }

  metric_query {
    id = "m1"

    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ELB"
      period      = "300"
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        LoadBalancerName = var.api_elb
      }
    }
  }

  metric_query {
    id = "m2"

    metric {
      metric_name = "HealthyHostCount"
      namespace   = "AWS/ELB"
      period      = "300"
      stat        = "Average"
      unit        = "Count"

      dimensions = {
        LoadBalancerName = var.api_elb
      }
    }
  }

  alarm_description = "Request Count per Instance Greater Than 10000 on ${var.api_name_prefix}"
  alarm_actions     = [aws_autoscaling_policy.api_scale_up.arn]
}

resource "aws_autoscaling_policy" "api_scale_down" {
  name                   = "${var.api_name_prefix}_scaledown (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.api_asg.name
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_low_requests" {
  alarm_name          = "${var.api_name_prefix}_requestslow (${var.aws_amis[var.aws_region]})"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "2"
  threshold           = "10000"

  metric_query {
    id          = "e1"
    expression  = "m1/m2"
    label       = "Requests Per Host"
    return_data = "true"
  }

  metric_query {
    id = "m1"

    metric {
      metric_name = "RequestCount"
      namespace   = "AWS/ELB"
      period      = "300"
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        LoadBalancerName = var.api_elb
      }
    }
  }

  metric_query {
    id = "m2"

    metric {
      metric_name = "HealthyHostCount"
      namespace   = "AWS/ELB"
      period      = "300"
      stat        = "Average"
      unit        = "Count"

      dimensions = {
        LoadBalancerName = var.api_elb
      }
    }
  }

  alarm_description = "Request Count per Instance Less Than 10000 on ${var.api_name_prefix}"
  alarm_actions     = [aws_autoscaling_policy.api_scale_down.arn]
}

resource "aws_autoscaling_group" "bd_asg" {
  name                      = "${var.bd_name_prefix} (${var.aws_amis[var.aws_region]})"
  max_size                  = var.bd_asg_max
  min_size                  = var.bd_asg_min
  desired_capacity          = var.bd_asg_desired
  enabled_metrics           = split(",", var.bd_enabled_metrics)
  health_check_type         = "EC2"
  health_check_grace_period = 0
  launch_configuration      = aws_launch_configuration.bd_lc.name
  vpc_zone_identifier       = split(",", var.subnets)

  tags = [
    {
      key                   = "Name"
      value                 = "${var.bd_name_prefix} (${var.aws_amis[var.aws_region]})"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Application"
      value                 = "USAspending"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Component"
      value                 = "BulkDownload"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Environment"
      value                 =  var.env_tag
      propagate_at_launch   = "true"
    },
  ]

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_launch_configuration" "bd_lc" {
  name                 = "${var.bd_name_prefix} (${var.aws_amis[var.aws_region]})"
  image_id             = var.aws_amis[var.aws_region]
  instance_type        = var.bd_instance_type
  iam_instance_profile = var.iam_profile
  security_groups      = split(",", var.sec_groups)
  user_data            = var.bd_user_data
  key_name             = var.key_name
  ebs_optimized        = true
  lifecycle {
    create_before_destroy = true
  }
  root_block_device {
    volume_size = var.bd_ebs_size
    volume_type = var.bd_ebs_type
  }
}

resource "aws_autoscaling_policy" "bd_scale_up" {
  name                   = "${var.bd_name_prefix}_scaleup (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.bd_asg.name
}

resource "aws_autoscaling_policy" "bd_scale_down" {
  name                   = "${var.bd_name_prefix}_scaledown (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 30
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.bd_asg.name
}

resource "aws_cloudwatch_metric_alarm" "bd_sqs_queue_low" {
  alarm_name          = "${var.bd_name_prefix}_queue_low (${var.aws_amis[var.aws_region]})"
  alarm_description   = <<EOF
    The messages in flight average is now below 5 for the previous 10 minutes. 
  EOF
  comparison_operator = "LessThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.bd_scale_down.arn]
  evaluation_periods  = "2"
  threshold           = "5"

  metric_query {
    id          = "e1"
    expression  = "m1/m2"
    label       = "Average in flight per host"
    return_data = "true"
  }

  metric_query {
    id = "m1"

    metric {
      metric_name = "ApproximateNumberOfMessagesNotVisible"
      namespace   = "AWS/SQS"
      period      = "300"
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        QueueName = "usaspending-bulk-download-${var.env_tag}"
      }
    }
  }

  metric_query {
    id = "m2"

    metric {
      metric_name = "GroupInServiceInstances"
      namespace   = "AWS/AutoScaling"
      period      = "300"
      stat        = "Maximum"

      dimensions = {
        AutoScalingGroupName = aws_autoscaling_group.bd_asg.name
      }
    }
  }
}

resource "aws_cloudwatch_metric_alarm" "bd_sqs_queue_high" {
  alarm_name          = "${var.bd_name_prefix}_queue_high (${var.aws_amis[var.aws_region]})"
  alarm_description   = <<EOF
    The messages in flight average is now above 5 for more than 10 minutes. 
  EOF
  comparison_operator = "GreaterThanThreshold"
  alarm_actions       = [aws_autoscaling_policy.bd_scale_up.arn]
  evaluation_periods  = "2"
  threshold           = "5"

  metric_query {
    id          = "e1"
    expression  = "m1/m2"
    label       = "Average in flight per host"
    return_data = "true"
  }

  metric_query {
    id = "m1"

    metric {
      metric_name = "ApproximateNumberOfMessagesNotVisible"
      namespace   = "AWS/SQS"
      period      = "300"
      stat        = "Sum"
      unit        = "Count"

      dimensions = {
        QueueName = "usaspending-bulk-download-${var.env_tag}"
      }
    }
  }

  metric_query {
    id = "m2"

    metric {
      metric_name = "GroupInServiceInstances"
      namespace   = "AWS/AutoScaling"
      period      = "300"
      stat        = "Maximum"

      dimensions = {
        AutoScalingGroupName = aws_autoscaling_group.bd_asg.name
      }
    }
  }
}
