import cloud
import argparse

if __name__ == '__main__':

    # Arguments
    parser = argparse.ArgumentParser(
            description='manage and deploy to application infrastructure.',
            epilog='For info on instances, see https://aws.amazon.com/ec2/instance-types/instance-details/'
            )
    # Required
    parser.add_argument('env', metavar='env', type=str, help='the environment, e.g. production, qa')
    parser.add_argument('command', metavar='command', type=str, help='the command to perform.', choices=['commission', 'decommission', 'deploy', 'clean'])

    # Optional
    parser.add_argument('-ssh', help='enable ssh on app and master instances', action='store_true', default=False)
    parser.add_argument('--min_size', type=int, help='the minimum autoscaling size', default=1)
    parser.add_argument('--max_size', type=int, help='the maximum autoscaling size', default=4)
    parser.add_argument('--instance_type', type=str, help='the instance type for the application infrastructure', default='m1.medium')
    args = parser.parse_args()

    if args.command == 'commission':
        cloud.commission(
            args.env,
            instance_type=args.instance_type,
            min_size=args.min_size,
            max_size=args.max_size,
            ssh=args.ssh)

    elif args.command == 'decommission':
        confirm = input('This will dismantle the application infrastructure for {0}. Are you sure? '.format(args.env))
        if confirm.lower() in ['y', 'yes', 'yeah', 'ya', 'aye']:
            cloud.decommission(args.env)
        else:
            print('Exiting.')

    elif args.command == 'deploy':
        cloud.deploy(args.env)

    elif args.command == 'clean':
        cloud.clean(args.env)
