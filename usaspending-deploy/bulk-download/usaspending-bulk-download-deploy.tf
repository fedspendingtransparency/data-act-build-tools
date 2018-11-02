provider "aws" {
    region = "${var.aws_region}"
}

terraform {
  backend "s3" {}
}

resource "aws_autoscaling_group" "bd-asg" {
  name = "${var.bd_name_prefix}_${lookup(var.aws_amis, var.aws_region)}"
  max_size = "${var.bd_asg_max}"
  min_size = "${var.bd_asg_min}"
  desired_capacity = "${var.bd_asg_desired}"
  health_check_type = "EC2"
  health_check_grace_period = 0
  launch_configuration = "${aws_launch_configuration.bd-lc.name}"
  vpc_zone_identifier = ["${split(",", var.subnets)}"]

  tag = {
      key = "Name"
      value = "${var.bd_name_prefix}_${lookup(var.aws_amis, var.aws_region)}"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Application"
      value = "USAspending"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Component"
      value = "BulkDownload"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Environment"
      value = "${var.bd_env_tag}"
      propagate_at_launch = "true"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_launch_configuration" "bd-lc" {
  name = "${var.bd_name_prefix}_${lookup(var.aws_amis, var.aws_region)}"
  image_id = "${lookup(var.aws_amis, var.aws_region)}"
  instance_type = "${var.bd_instance_type}"
  iam_instance_profile = "${var.bd_iam_profile}"
  security_groups = ["${split(",", var.bd_sec_groups)}"]
  user_data = "${var.user_data}"
  key_name = "${var.key_name}"
  lifecycle {
    create_before_destroy = true
  }
  root_block_device {
    volume_size = "${var.bd_ebs_size}"
    volume_type = "${var.bd_ebs_type}"
  }
}

resource "aws_autoscaling_policy" "bd_scale_up" {
  name                   = "${var.bd_name_prefix}_scaleup_${lookup(var.aws_amis, var.aws_region)}"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.bd-asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "bd_alarm_high_cpu" {
  alarm_name          = "${var.bd_name_prefix}_cpuhigh_${lookup(var.aws_amis, var.aws_region)}"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "50"

  dimensions {
    AutoScalingGroupName = "${aws_autoscaling_group.bd-asg.name}"
  }

  alarm_description = "High CPU on ${var.bd_name_prefix}"
  alarm_actions     = ["${aws_autoscaling_policy.bd_scale_up.arn}"]
}

resource "aws_autoscaling_policy" "bd_scale_down" {
  name                   = "${var.bd_name_prefix}_scaledown_${lookup(var.aws_amis, var.aws_region)}"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 30
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.bd-asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "bd_alarm_low_cpu" {
  alarm_name          = "${var.bd_name_prefix}_cpulow_${lookup(var.aws_amis, var.aws_region)}"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "5"

  dimensions {
    AutoScalingGroupName = "${aws_autoscaling_group.bd-asg.name}"
  }

  alarm_description = "All Instance CPU low ${var.bd_name_prefix}"
  alarm_actions     = ["${aws_autoscaling_policy.bd_scale_down.arn}"]
}
