# Terraform deployment file
# Separate variables definitions required

provider "aws" {
  region = var.aws_region
}

terraform {
  backend "s3" {}
}

resource "aws_autoscaling_group" "api-asg" {
  name                      = aws_launch_configuration.api-lc.name
  max_size                  = var.api_asg_max
  min_size                  = var.api_asg_min
  desired_capacity          = var.api_asg_desired
  min_elb_capacity          = var.api_asg_min
  health_check_type         = "ELB"
  health_check_grace_period = 180
  launch_configuration      = aws_launch_configuration.api-lc.name
  load_balancers            = [var.api_elb]
  vpc_zone_identifier       = split(",", var.subnets)

  tags = [
    {
      key                   = "Name"
      value                 = "${var.api_name_prefix} (${var.aws_amis[var.aws_region]})"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Application"
      value                 = "Broker"
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

resource "aws_autoscaling_group" "val-asg" {
  name                      = aws_launch_configuration.val-lc.name
  max_size                  = var.val_asg_max
  min_size                  = var.val_asg_min
  desired_capacity          = var.val_asg_desired
  min_elb_capacity          = var.val_asg_min
  health_check_type         = "ELB"
  health_check_grace_period = 180
  launch_configuration      = aws_launch_configuration.val-lc.name
  load_balancers            = [var.val_elb]
  vpc_zone_identifier       = split(",", var.subnets)

  tags = [
    {
      key                   = "Name"
      value                 = "${var.val_name_prefix} (${var.aws_amis[var.aws_region]})"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Application"
      value                 = "Broker"
      propagate_at_launch   = "true"
    },
    {
      key                   = "Component"
      value                 = "Validator"
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

resource "aws_launch_configuration" "api-lc" {
  name                 = "${var.api_name_prefix} (${var.aws_amis[var.aws_region]})"
  image_id             = var.aws_amis[var.aws_region]
  instance_type        = var.api_instance_type
  iam_instance_profile = var.api_iam_profile

  # Security group
  security_groups = split(",", var.api_sec_groups)
  user_data       = file("broker-start-api.sh")
  key_name        = var.key_name
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_launch_configuration" "val-lc" {
  name                 = "${var.val_name_prefix} (${var.aws_amis[var.aws_region]})"
  image_id             = var.aws_amis[var.aws_region]
  instance_type        = var.val_instance_type
  iam_instance_profile = var.val_iam_profile

  # Security group
  security_groups = split(",", var.val_sec_groups)
  user_data       = file("broker-start-val.sh")
  key_name        = var.key_name
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_policy" "val_scale_up" {
  name                   = "${var.val_name_prefix}_scaleup (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.val-asg.name
}

resource "aws_cloudwatch_metric_alarm" "val_alarm_high_cpu" {
  alarm_name          = "${var.val_name_prefix}_cpuhigh (${var.aws_amis[var.aws_region]})"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "75"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.val-asg.name
  }

  alarm_description = "High CPU over 75% on ${var.val_name_prefix}"
  alarm_actions     = [aws_autoscaling_policy.val_scale_up.arn]
}

resource "aws_autoscaling_policy" "api_scale_up" {
  name                   = "${var.api_name_prefix}_scaleup (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.api-asg.name
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_high_cpu" {
  alarm_name          = "${var.api_name_prefix}_cpuhigh (${var.aws_amis[var.aws_region]})"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Average"
  threshold           = "75"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.api-asg.name
  }

  alarm_description = "High CPU over 75% on ${var.api_name_prefix}"
  alarm_actions     = [aws_autoscaling_policy.api_scale_up.arn]
}

resource "aws_autoscaling_policy" "api_scale_down" {
  name                   = "${var.api_name_prefix}_scaledown (${var.aws_amis[var.aws_region]})"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 30
  policy_type            = "SimpleScaling"
  autoscaling_group_name = aws_autoscaling_group.api-asg.name
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_low_cpu" {
  alarm_name          = "${var.api_name_prefix}_cpulow (${var.aws_amis[var.aws_region]})"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "5"

  dimensions = {
    AutoScalingGroupName = aws_autoscaling_group.api-asg.name
  }

  alarm_description = "All Instance CPU below 5% on ${var.api_name_prefix}"
  alarm_actions     = [aws_autoscaling_policy.api_scale_down.arn]
}

