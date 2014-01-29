from cloud import connect

import logging
logger = logging.getLogger(__name__)

def autoscaling_group_exists(name):
    """
    Checks if the AutoScale Group exists.

    Args:
        | name (str)    -- name of the autoscaling group to look for.

    Returns:
        | int   -- number of AutoScale Groups found.
    """
    asg = connect.asg()

    groups = asg.get_all_groups(names=[name])
    return len(groups)


def delete_autoscaling_group(name, launch_config_name):
    asg = connect.asg()
    ec2 = connect.ec2()

    # Delete alarms.
    logger.info('Deleting CloudWatch MetricAlarms...')
    cloudwatch = connect.clw()
    cloudwatch.delete_alarms(['scale-up-on-cpu', 'scale-down-on-cpu'])

    # Shutdown and delete autoscaling groups.
    # This also deletes the groups' scaling policies.
    logger.info('Deleting the autoscaling group ({0})...'.format(name))
    groups = asg.get_all_groups(names=[name])
    for group in groups:
        group_instance_ids = [i.instance_id for i in group.instances]

        # Shutdown all group instances.
        logger.info('Terminating group instances...')
        group.shutdown_instances()

        # If there are still instances left in the group,
        # wait until they shut down.
        if group_instance_ids:
            group_instances = [r.instances[0] for r in ec2.get_all_instances(instance_ids=group_instance_ids)]

            logger.info('Waiting for group instances to shutdown...')
            manage.wait_until_terminated(group_instances)

        # Wait until all group activities have stopped.
        group_activities = group.get_activities()
        while group_activities:
            time.sleep(10)
            group_activities = [a for a in group.get_activities() if a.status_code == 'InProgress']

        # Delete the group.
        group.delete()

    # Delete launch configs.
    logger.info('Deleting the launch configuration ({0})...'.format(launch_config_name))
    launch_configs = asg.get_all_launch_configurations(names=[launch_config_name])
    for lc in launch_configs:
        lc.delete()


def create_autoscaling_group(name, image_id, init_script, launch_config_name, security_group_name, keypair_name, instance_type='m1.medium', min_size=1, max_size=4):
    """
    Create an autoscaling group.

    Args:
        | image_id              -- the AMI ID to use for the groups' instances
        | init_script           -- the initialization script for the groups' instances
        | launch_config_name    -- the name of the launch configuration
        | security_group_name   -- the name of the security group
        | keypair_name (str)    -- name of the keypair
        | instance_type (str)   -- the instance type (default: m1.medium)
    """
    asg = connect.asg()
    ec2 = connect.ec2()

    # Get availability zones for region.
    zones = [zone.name for zone in ec2.get_all_zones()]

    # Create the launch configuration.
    logger.info('Creating the launch configuration ({0})...'.format(launch_config_name))
    logger.info('Cloud is composed of {0} instances.'.format(instance_type))
    launch_config = LaunchConfiguration(
                        name=launch_config_name,
                        image_id=image_id,                      # AMI ID for autoscaling instances.
                        key_name=keypair_name,                  # The name of the EC2 keypair.
                        user_data=init_script,                  # User data: the initialization script for the instances.
                        security_groups=[security_group_name],  # Security groups the instance will be in.
                        instance_type=instance_type,            # Instance size.
                        instance_monitoring=True                # Enable monitoring (for CloudWatch).
                    )

    # Create the launch configuration on AWS.
    asg.create_launch_configuration(launch_config)


    # Create the autoscaling group.
    logger.info('Creating autoscaling group ({0})...'.format(name))
    autoscaling_group = AutoScalingGroup(
                            group_name=name,
                            availability_zones=zones,
                            launch_config=launch_config,
                            min_size=min_size,  # minimum group size
                            max_size=max_size,  # maximum group size
                            connection=asg
                        )

    # Create the autoscaling group on AWS.
    asg.create_auto_scaling_group(autoscaling_group)

    # Create the scaling policies.
    # These scaling policies change the size of the group.
    logger.info('Creating scaling policies...')
    scale_up_policy = ScalingPolicy(
                          name='scale-up',
                          adjustment_type='ChangeInCapacity',
                          as_name=name,
                          scaling_adjustment=1,
                          cooldown=180
                      )
    scale_dn_policy = ScalingPolicy(
                          name='scale-down',
                          adjustment_type='ChangeInCapacity',
                          as_name=name,
                          scaling_adjustment=-1,
                          cooldown=180
                      )

    # Create the scaling policies on AWS.
    asg.create_scaling_policy(scale_up_policy)
    asg.create_scaling_policy(scale_dn_policy)

    # Some extra parameters are created on the policies
    # after they are created on AWS. We need to re-fetch them
    # to edit them.
    scale_up_policy = asg.get_all_policies(
                          as_group=name,
                          policy_names=['scale-up']
                      )[0]
    scale_dn_policy = asg.get_all_policies(
                          as_group=name,
                          policy_names=['scale-down']
                      )[0]

    # Create CloudWatch alarms.
    logger.info('Creating CloudWatch MetricAlarms...')
    cloudwatch = connect.clw()

    # We need to specify the "dimensions" of this alarm,
    # which describes what it watches (here, the whole autoscaling group).
    alarm_dimensions = {'AutoScalingGroupName': name}

    # Create the scale up alarm.
    # Scale up when average CPU utilization becomes greater than 70%.
    scale_up_alarm = MetricAlarm(
                        name='scale-up-on-cpu',
                        namespace='AWS/EC2',
                        metric='CPUUtilization',
                        statistic='Average',
                        comparison='>',
                        threshold='70',
                        period='60',
                        evaluation_periods=2,
                        alarm_actions=[scale_up_policy.policy_arn],
                        dimensions=alarm_dimensions
                     )
    cloudwatch.create_alarm(scale_up_alarm)

    # Create the scale down alarm.
    # Scale down when average CPU utilization becomes less than 40%.
    scale_dn_alarm = MetricAlarm(
                        name='scale-down-on-cpu',
                        namespace='AWS/EC2',
                        metric='CPUUtilization',
                        statistic='Average',
                        comparison='<',
                        threshold='40',
                        period='60',
                        evaluation_periods=2,
                        alarm_actions=[scale_dn_policy.policy_arn],
                        dimensions=alarm_dimensions
                     )
    cloudwatch.create_alarm(scale_dn_alarm)
