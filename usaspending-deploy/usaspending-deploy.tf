provider "aws" {
    region = "${var.aws_region}"
}

terraform {
  backend "s3" {}
}

resource "aws_autoscaling_group" "api-asg" {
  name = "${var.api_name_prefix}_ASG_${lookup(var.aws_amis, var.aws_region)}"
  max_size = "${var.api_asg_max}"
  min_size = "${var.api_asg_min}"
  desired_capacity = "${var.api_asg_desired}"
  min_elb_capacity = "${var.api_asg_min}"
  health_check_type = "ELB"
  health_check_grace_period = 30
  launch_configuration = "${aws_launch_configuration.api-lc.name}"
  load_balancers = ["${var.api_elb}"]
  vpc_zone_identifier = ["${split(",", var.subnets)}"]
    
  tag = {
      key = "Name"
      value = "${var.api_name_prefix}_ASG"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Application"
      value = "USAspending"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Component"
      value = "API"
      propagate_at_launch = "true"
  }
  tag = {
      key = "Environment"
      value = "${var.api_env_tag}"
      propagate_at_launch = "true"
  }
    
  lifecycle {
    create_before_destroy = true
  }
    
}

resource "aws_launch_configuration" "api-lc" {
  name = "${var.api_name_prefix}_LC_${lookup(var.aws_amis, var.aws_region)}"
  image_id = "${lookup(var.aws_amis, var.aws_region)}"
  instance_type = "${var.api_instance_type}"
  ebs_optimized = true
  iam_instance_profile = "${var.api_iam_profile}"
  security_groups = ["${split(",", var.api_sec_groups)}"]
  user_data = "${file("usaspending-start-staging.sh")}"
  key_name = "${var.key_name}"
  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_autoscaling_policy" "api_scale_up" {
  name                   = "${var.api_name_prefix}_ScaleUp"
  scaling_adjustment     = 1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 300
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.api-asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_high_cpu" {
  alarm_name          = "${var.api_name_prefix}_HighCPU"
  comparison_operator = "GreaterThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "120"
  statistic           = "Average"
  threshold           = "50"

  dimensions {
    AutoScalingGroupName = "${aws_autoscaling_group.api-asg.name}"
  }

  alarm_description = "High CPU on ${var.api_name_prefix}"
  alarm_actions     = ["${aws_autoscaling_policy.api_scale_up.arn}"]
}

resource "aws_autoscaling_policy" "api_scale_down" {
  name                   = "${var.api_name_prefix}_ScaleDown"
  scaling_adjustment     = -1
  adjustment_type        = "ChangeInCapacity"
  cooldown               = 30
  policy_type            = "SimpleScaling"
  autoscaling_group_name = "${aws_autoscaling_group.api-asg.name}"
}

resource "aws_cloudwatch_metric_alarm" "api_alarm_low_cpu" {
  alarm_name          = "${var.api_name_prefix}_LowCPU"
  comparison_operator = "LessThanOrEqualToThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/EC2"
  period              = "60"
  statistic           = "Maximum"
  threshold           = "5"

  dimensions {
    AutoScalingGroupName = "${aws_autoscaling_group.api-asg.name}"
  }

  alarm_description = "All Instance CPU low ${var.api_name_prefix}"
  alarm_actions     = ["${aws_autoscaling_policy.api_scale_down.arn}"]
}
