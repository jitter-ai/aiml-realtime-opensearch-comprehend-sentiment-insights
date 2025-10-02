from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
import boto3
import sys
import json
import subprocess
import logging
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from botocore.exceptions import ClientError
import readchar
from functools import wraps

# Check if required packages are installed
try:
    from rich.console import Console
    from rich.logging import RichHandler
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from pydantic import BaseModel, Field
    DEPENDENCIES_INSTALLED = True
except ImportError:
    print("Required dependencies not found. Installing...")
    DEPENDENCIES_INSTALLED = False
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--no-cache-dir", "pydantic>=2.0.0", "rich>=13.0.0"])
        print("Dependencies installed successfully!")
        from rich.console import Console
        from rich.logging import RichHandler
        from rich.progress import Progress, SpinnerColumn, TextColumn
        from pydantic import BaseModel, Field
        DEPENDENCIES_INSTALLED = True
    except Exception as e:
        print(f"Failed to install dependencies: {e}")
        print("Please run: pip install pydantic rich")
        sys.exit(1)

from concurrent.futures import ThreadPoolExecutor
from boto3.session import Session

# Initialize Rich console
console = Console()

# Configure rich logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("deploy")

class AssetInfo(BaseModel):
    """Model for asset information"""
    local_path: str
    s3_key: str

class Assets(BaseModel):
    """Model for all assets"""
    lambda_function: AssetInfo
    lambda_layers: Dict[str, AssetInfo]

class DeploymentConfig(BaseModel):
    """Pydantic model for deployment configuration"""
    aws: Dict[str, str]
    assets: Assets
    template_path: str
    stack_parameters: List[Dict[str, str]]
    stack_capabilities: List[str]
    waiter_config: Dict[str, int]

@dataclass
class AWSContext:
    """Context manager for AWS session and resources"""
    session: Session
    profile: str
    region: str
    account_id: str

def error_handler(func):
    """Decorator for consistent error handling"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error in {func.__name__}")
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            sys.exit(1)
    return wrapper

@error_handler
def load_config() -> DeploymentConfig:
    """Load and validate deployment configuration"""
    script_dir = Path(__file__).parent
    config_path = script_dir.parent / "config" / "deployment_config.json"
    logger.debug(f"Loading config from: {config_path}")

    # Try to open the config file
    try:
        with open(config_path, 'r') as f:
            data = json.load(f)
            return DeploymentConfig.model_validate(data)
    except FileNotFoundError:
        # Try an alternative location
        console.print(f"[yellow]Config not found at {config_path}, trying alternative location...[/yellow]")
        config_path = script_dir.parent / "deployment_config.json"
        logger.debug(f"Trying alternative config path: {config_path}")
        with open(config_path, 'r') as f:
            data = json.load(f)
            return DeploymentConfig.model_validate(data)

class AWSProfileManager:
    """Manages AWS profile selection and session creation"""
    @staticmethod
    @error_handler
    def get_profiles() -> List[str]:
        result = subprocess.run(
            ['aws', 'configure', 'list-profiles'],
            capture_output=True, text=True, check=True
        )
        return [p for p in result.stdout.strip().split('\n') if p]

    @staticmethod
    @error_handler
    def create_session(profile: str, region: str) -> AWSContext:
        session = boto3.Session(profile_name=profile, region_name=region)
        sts = session.client('sts')
        identity = sts.get_caller_identity()

        return AWSContext(
            session=session,
            profile=profile,
            region=region,
            account_id=identity['Account']
        )

class S3Manager:
    """Manages S3 operations with progress tracking"""
    def __init__(self, aws_context: AWSContext):
        self.context = aws_context
        self.s3 = aws_context.session.client('s3')
        self.bucket_name = f"aos-artifacts-{aws_context.account_id}-{aws_context.region}"

    @error_handler
    def ensure_bucket(self, status=None) -> bool:
        """Ensure S3 bucket exists"""
        if status:
            status.update("Checking bootstrap bucket...")
        else:
            console.print("Checking bootstrap bucket...")

        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            console.print(f"[green]✓ Bucket {self.bucket_name} exists[/green]")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise

            if status:
                status.update("Creating bucket...")
            else:
                console.print("Creating bucket...")

            create_args = {
                'Bucket': self.bucket_name,
                **(
                    {'CreateBucketConfiguration': {'LocationConstraint': self.context.region}}
                    if self.context.region != "us-east-1"
                    else {}
                )
            }
            self.s3.create_bucket(**create_args)
            console.print(f"[green]✓ Created bucket {self.bucket_name}[/green]")
            return True

    @error_handler
    def upload_assets(self, assets: Assets, status=None) -> None:
        """Upload assets with parallel processing"""
        def upload_single_asset(asset_info: AssetInfo, asset_name=""):
            script_dir = Path(__file__).parent.parent

            # List of possible paths to try
            possible_paths = [
                # Try in dependencies directory with the asset path
                script_dir / "dependencies" / asset_info.local_path,
                # Try directly in dependencies directory
                script_dir / "dependencies" / Path(asset_info.local_path).name,
                # Try in lambda_function directory inside dependencies
                script_dir / "dependencies" / "lambda_function" / Path(asset_info.local_path).name,
                # Try in lambda_layers directory inside dependencies
                script_dir / "dependencies" / "lambda_layers" / Path(asset_info.local_path).name,
                # Original path as fallback
                script_dir / asset_info.local_path
            ]

            # Try each path
            for path in possible_paths:
                logger.debug(f"Checking path: {path}")
                if path.exists():
                    logger.debug(f"Found asset at: {path}")
                    local_path = path
                    break
            else:
                # If no path exists, raise an error
                console.print(f"[yellow]Debug: Current directory: {Path.cwd()}[/yellow]")
                console.print(f"[yellow]Debug: Script directory: {script_dir}[/yellow]")
                console.print(f"[yellow]Debug: Asset path from config: {asset_info.local_path}[/yellow]")
                # List the contents of the dependencies directory
                deps_dir = script_dir / "dependencies"
                if deps_dir.exists():
                    console.print(f"[yellow]Debug: Contents of {deps_dir}:[/yellow]")
                    for item in deps_dir.iterdir():
                        console.print(f"[yellow]  - {item.name}[/yellow]")
                        if item.is_dir():
                            for subitem in item.iterdir():
                                console.print(f"[yellow]    - {subitem.name}[/yellow]")
                raise FileNotFoundError(f"Asset not found. Tried: {possible_paths}")

            if status:
                status.update(f"Uploading {asset_name or 'asset'}...")
            else:
                console.print(f"Uploading {asset_name or 'asset'}...")

            command = [
                "aws", "s3", "cp",
                str(local_path),
                f"s3://{self.bucket_name}/{asset_info.s3_key}",
                "--profile", self.context.profile
            ]
            subprocess.run(command, check=True)
            return asset_info.s3_key

        # Upload lambda function
        upload_single_asset(assets.lambda_function, "lambda function")

        # Upload lambda layers
        for layer_name, layer_info in assets.lambda_layers.items():
            upload_single_asset(layer_info, f"layer: {layer_name}")

class CloudFormationMonitor:
    """Monitors CloudFormation stack operations"""
    def __init__(self, cf_client, profile: str):
        self.cf = cf_client
        self.profile = profile
        self.status_colors = {
            'CREATE_COMPLETE': '[green]',
            'UPDATE_COMPLETE': '[green]',
            'DELETE_COMPLETE': '[green]',
            'CREATE_IN_PROGRESS': '[blue]',
            'UPDATE_IN_PROGRESS': '[blue]',
            'DELETE_IN_PROGRESS': '[blue]',
            'ROLLBACK_IN_PROGRESS': '[yellow]',
            'ROLLBACK_COMPLETE': '[red]',
            'UPDATE_ROLLBACK_IN_PROGRESS': '[yellow]',
            'UPDATE_ROLLBACK_COMPLETE': '[red]',
            'CREATE_FAILED': '[red]',
            'DELETE_FAILED': '[red]',
            'UPDATE_FAILED': '[red]',
        }

    def get_stack_status(self, stack_name: str) -> Tuple[str, bool]:
        """Get the current status of a stack"""
        try:
            response = self.cf.describe_stacks(StackName=stack_name)
            status = response['Stacks'][0]['StackStatus']
            is_complete = not status.endswith('_IN_PROGRESS')
            return status, is_complete
        except ClientError as e:
            console.print(f"[red]Error getting stack status: {str(e)}[/red]")
            return "UNKNOWN", True  # Return as complete to exit the monitoring loop

    def get_recent_events(self, stack_name: str, since: datetime) -> List[Dict]:
        """Get stack events since the specified time"""
        try:
            events = self.cf.describe_stack_events(StackName=stack_name)['StackEvents']
            return [e for e in events if e['Timestamp'] > since]
        except ClientError as e:
            console.print(f"[red]Error getting stack events: {str(e)}[/red]")
            return []

    def print_event(self, event: Dict) -> None:
        """Print a formatted stack event"""
        status = event['ResourceStatus']
        resource_type = event['ResourceType']
        logical_id = event['LogicalResourceId']

        # Get color for status
        color = self.status_colors.get(status, '[white]')

        # Format and print the event
        console.print(f"{color}{status}[/] - {resource_type} - {logical_id}")

        # Print reason if available
        if 'ResourceStatusReason' in event and event['ResourceStatusReason']:
            console.print(f"  Reason: {event['ResourceStatusReason']}")

    def monitor_stack(self, stack_name: str, status=None) -> bool:
        """Monitor stack events and status until completion"""
        console.print("\nMonitoring stack events:")
        last_event_time = datetime.now(timezone.utc) - timedelta(seconds=30)

        while True:
            # Get and print new events
            new_events = self.get_recent_events(stack_name, last_event_time)
            for event in sorted(new_events, key=lambda e: e['Timestamp']):
                self.print_event(event)
                last_event_time = max(last_event_time, event['Timestamp'])

            # Check stack status
            current_status, is_complete = self.get_stack_status(stack_name)

            if status:
                status.update(f"Stack status: {current_status}")

            if is_complete:
                # Stack operation is complete
                success = current_status.endswith('_COMPLETE') and not current_status.endswith('ROLLBACK_COMPLETE')
                return success

            # Wait before checking again
            time.sleep(10)

class CloudFormationManager:
    """Manages CloudFormation stack operations"""
    def __init__(self, aws_context: AWSContext, config: DeploymentConfig):
        self.cf = aws_context.session.client('cloudformation')
        self.config = config
        self.stack_name = config.aws['stack_name']
        self.context = aws_context

    @error_handler
    def deploy_stack(self, status=None) -> None:
        """Deploy or update CloudFormation stack"""
        if status:
            status.update("Deploying stack...")
        else:
            console.print("Deploying stack...")

        script_dir = Path(__file__).parent.parent
        # Try to find the template in the config directory first
        template_path = script_dir / "config" / self.config.template_path
        if not template_path.exists():
            # Fallback to the original path
            template_path = script_dir / self.config.template_path
            if not template_path.exists():
                raise FileNotFoundError(f"Template not found: {template_path}")
        template_body = template_path.read_text()

        # Add bucket name to parameters
        parameters = self.config.stack_parameters.copy()
        parameters.append({
            'ParameterKey': 'MyAssetsBucketName',
            'ParameterValue': f"aos-artifacts-{self.context.account_id}-{self.context.region}"
        })

        stack_params = {
            'StackName': self.stack_name,
            'TemplateBody': template_body,
            'Capabilities': self.config.stack_capabilities,
            'Parameters': parameters
        }

        try:
            self.cf.create_stack(**stack_params)
            if status:
                status.update("Creating stack...")
            else:
                console.print("Creating stack...")
            waiter = self.cf.get_waiter('stack_create_complete')
        except ClientError as e:
            if e.response['Error']['Code'] != 'AlreadyExistsException':
                raise
            try:
                self.cf.update_stack(**stack_params)
                if status:
                    status.update("Updating stack...")
                else:
                    console.print("Updating stack...")
                waiter = self.cf.get_waiter('stack_update_complete')
            except ClientError as e:
                if 'No updates are to be performed' in str(e):
                    console.print("[yellow]No updates needed for the stack[/yellow]")
                    return
                raise

        # Use the stack monitor instead of the waiter
        stack_monitor = CloudFormationMonitor(self.cf, self.context.profile)
        success = stack_monitor.monitor_stack(self.stack_name, status)

        if success:
            console.print("[green]✓ Stack deployment completed successfully[/green]")
        else:
            console.print("[red]❌ Stack deployment failed[/red]")
            sys.exit(1)

class ResourceCleanup:
    """Handles cleanup of AWS resources"""
    def __init__(self, aws_context: AWSContext):
        self.context = aws_context
        self.s3 = aws_context.session.client('s3')
        self.cf = aws_context.session.client('cloudformation')
        self.lambda_client = aws_context.session.client('lambda')

    @error_handler
    def empty_s3_bucket(self, bucket_name: str, status=None) -> bool:
        """Empty an S3 bucket before deletion"""
        if status:
            status.update(f"Emptying bucket {bucket_name}...")
        else:
            console.print(f"Emptying bucket {bucket_name}...")

        try:
            # List all objects in the bucket
            paginator = self.s3.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket_name):
                if 'Contents' not in page:
                    continue

                # Delete objects
                objects = [{'Key': obj['Key']} for obj in page['Contents']]
                self.s3.delete_objects(
                    Bucket=bucket_name,
                    Delete={'Objects': objects}
                )

            # List and delete all object versions (if versioning is enabled)
            paginator = self.s3.get_paginator('list_object_versions')
            for page in paginator.paginate(Bucket=bucket_name):
                delete_keys = []

                # Add object versions
                if 'Versions' in page:
                    for version in page['Versions']:
                        delete_keys.append({
                            'Key': version['Key'],
                            'VersionId': version['VersionId']
                        })

                # Add delete markers
                if 'DeleteMarkers' in page:
                    for marker in page['DeleteMarkers']:
                        delete_keys.append({
                            'Key': marker['Key'],
                            'VersionId': marker['VersionId']
                        })

                if delete_keys:
                    self.s3.delete_objects(
                        Bucket=bucket_name,
                        Delete={'Objects': delete_keys}
                    )

            console.print(f"[green]✓ Bucket {bucket_name} emptied[/green]")
            return True
        except ClientError as e:
            console.print(f"[red]Error emptying bucket: {str(e)}[/red]")
            return False

    @error_handler
    def delete_stack(self, stack_name: str, status=None) -> bool:
        """Delete a CloudFormation stack"""
        if status:
            status.update(f"Deleting stack {stack_name}...")
        else:
            console.print(f"Deleting stack {stack_name}...")

        try:
            # Check if stack exists
            self.cf.describe_stacks(StackName=stack_name)

            # Delete the stack
            self.cf.delete_stack(StackName=stack_name)

            # Monitor the deletion
            monitor = CloudFormationMonitor(self.cf, self.context.profile)
            success = monitor.monitor_stack(stack_name, status)

            if success:
                console.print(f"[green]✓ Stack {stack_name} deleted[/green]")
            else:
                console.print(f"[red]Failed to delete stack {stack_name}[/red]")

            return success
        except ClientError as e:
            if 'does not exist' in str(e):
                console.print(f"[yellow]Stack {stack_name} does not exist[/yellow]")
                return True
            console.print(f"[red]Error deleting stack: {str(e)}[/red]")
            return False

def main():
    """Main deployment process"""
    config = load_config()

    # Print debug information about the config
    logger.debug(f"Loaded config: {config}")
    console.print("[dim]Debug: Asset paths from config:[/dim]")
    console.print(f"[dim]  - Lambda function: {config.assets.lambda_function.local_path}[/dim]")
    for layer_name, layer_info in config.assets.lambda_layers.items():
        console.print(f"[dim]  - Layer {layer_name}: {layer_info.local_path}[/dim]")

    # Get AWS profiles and let user select one
    profiles = AWSProfileManager.get_profiles()
    if not profiles:
        console.print("[red]No AWS profiles found. Please configure AWS CLI first.[/red]")
        sys.exit(1)

    console.print("\nAvailable AWS profiles:")
    for i, profile in enumerate(profiles, 1):
        console.print(f"[cyan][{i}][/cyan] {profile}")

    while True:
        try:
            profile_idx = int(input("\nSelect profile number: "))
            if 1 <= profile_idx <= len(profiles):
                break
            console.print("[red]Invalid selection. Please try again.[/red]")
        except ValueError:
            console.print("[red]Please enter a valid number.[/red]")

    selected_profile = profiles[profile_idx - 1]

    # Initialize AWS context and managers
    aws_context = AWSProfileManager.create_session(selected_profile, config.aws['region'])
    s3_manager = S3Manager(aws_context)
    cf_manager = CloudFormationManager(aws_context, config)

    # Execute deployment steps
    with console.status("Deploying...") as status:
        if not s3_manager.ensure_bucket(status):
            sys.exit(1)

        status.update("Uploading assets...")
        s3_manager.upload_assets(config.assets, status)

        status.update("Deploying CloudFormation stack...")
        cf_manager.deploy_stack(status)

    console.print("\n[green]✓ Deployment completed successfully![/green]")

if __name__ == "__main__":
    main()
