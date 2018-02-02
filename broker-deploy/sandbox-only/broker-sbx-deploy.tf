provider "aws" {
    region = "us-gov-west-1"
}

resource "aws_eip_association" "eip_assoc" {
  instance_id   = "${aws_instance.broker-api-sandbox.id}"
  allocation_id = "${var.api_eip_alloc_id}"
}

resource "aws_instance" "broker-api-sandbox" {
  ami                   = "${var.base_ami}"
  instance_type         = "${var.api_instance_type}"
  subnet_id             = "${var.subnet}"
  key_name              = "${var.key_name}"
  security_groups       = ["${split(",", var.api_sec_groups)}"]
  iam_instance_profile  = "${var.api_iam_profile}"
  user_data	            = "${var.api_user_data}"

  tags {
    Name        = "${var.api_name}"
    Environment = "${var.env_tag}"
    Component   = "API"
    Application   = "Broker"
  }
}

resource "aws_instance" "broker-val-sandbox" {
  ami               	   = "${var.base_ami}"
  instance_type     	   = "${var.val_instance_type}"
  subnet_id         	   = "${var.subnet}"
  key_name				       = "${var.key_name}"
  security_groups		     = ["${split(",", var.val_sec_groups)}"]
  iam_instance_profile 	 = "${var.val_iam_profile}"
  user_data				       = "${var.val_user_data}"

  tags {
    Name          = "${var.val_name}"
    Environment   = "${var.env_tag}"
    Component     = "Validator"
    Application   = "Broker"
  }
}