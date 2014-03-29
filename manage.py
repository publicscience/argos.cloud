import cloud
import argparse

if __name__ == '__main__':

    # Arguments
    parser = argparse.ArgumentParser(
            description='manage and deploy to application infrastructure.',
            epilog='For info on instances, see https://aws.amazon.com/ec2/instance-types/instance-details/'
            )

    parser.add_argument('env', metavar='env', type=str, help='the environment, e.g. production, qa')
    subparsers = parser.add_subparsers(help='management commands', dest='command')

    # commission
    commission_parser = subparsers.add_parser('commission', help='commission new infrastructure')
    commission_parser.add_argument('--min_size', type=int, help='the minimum autoscaling size', default=1)
    commission_parser.add_argument('--max_size', type=int, help='the maximum autoscaling size', default=4)
    commission_parser.add_argument('--instance_type', type=str, help='the instance type for the application infrastructure', default='m3.medium')

    # decommission
    decommission_parser = subparsers.add_parser('decommission', help='decommissions infrastructure')

    # deploy
    deploy_parser = subparsers.add_parser('deploy', help='deploy to infrastructure')
    deploy_parser.add_argument('--role', type=str, help='the role to deploy', default='all', choices=['all', 'app', 'knowledge', 'collector'])

    # clean
    clean_parser = subparsers.add_parser('clean', help='cleans base images and image instances')

    args = parser.parse_args()

    if args.command == 'commission':
        cloud.commission(
            args.env,
            instance_type=args.instance_type,
            min_size=args.min_size,
            max_size=args.max_size)

    elif args.command == 'decommission':
        confirm = raw_input('This will dismantle the application infrastructure for [{0}]. Are you sure? '.format(args.env))
        if confirm.lower() in ['y', 'yes', 'yeah', 'ya', 'aye']:
            cloud.decommission(args.env)
        else:
            print('Exiting.')

    elif args.command == 'deploy':
        cloud.deploy(args.env, role=args.role)

    elif args.command == 'clean':
        confirm = raw_input('This will delete the base image for [{0}]. Are you sure? '.format(args.env))
        if confirm.lower() in ['y', 'yes', 'yeah', 'ya', 'aye']:
            cloud.clean()
        else:
            print('Exiting.')
