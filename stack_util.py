import boto3
import requests
import time
import sys
import questionary
import readchar
from datetime import datetime, timezone, timedelta
from botocore.exceptions import ClientError
from typing import Dict, List, Optional

class ConfigManager:
    """Handles configuration and user input"""
    
    @staticmethod
    def get_user_config() -> Dict[str, str]:
        """Get configuration from user input"""
        print("\n📝 Stack Configuration\n")
        
        # Default values
        defaults = {
            'template_url': "https://test-21212121.s3.us-east-1.amazonaws.com/sam.yml",
            'stack_name': "test",
            'bucket_name': "test-21212121",
            'bucket_prefix': ""
        }
        
        # Get user input with defaults
        config = {}
        config['template_url'] = questionary.text(
            "Template URL:",
            default=defaults['template_url']
        ).ask()
        
        config['stack_name'] = questionary.text(
            "Stack Name:",
            default=defaults['stack_name']
        ).ask()
        
        config['bucket_name'] = questionary.text(
            "Assets Bucket Name:",
            default=defaults['bucket_name']
        ).ask()
        
        config['bucket_prefix'] = questionary.text(
            "Assets Bucket Prefix:",
            default=defaults['bucket_prefix']
        ).ask()
        
        # Confirm configuration
        print("\n🔍 Configuration Summary:")
        for key, value in config.items():
            print(f"{key}: {value}")
            
        if not questionary.confirm("\nProceed with this configuration?").ask():
            print("Operation cancelled by user")
            sys.exit(0)
            
        return config

class StackMonitor:
    """Handles stack monitoring and status updates"""
    
    def __init__(self, cf_client):
        self.cf_client = cf_client
        self.colors = {
            'FAILED': '\033[91m',    # Red
            'COMPLETE': '\033[92m',  # Green
            'IN_PROGRESS': '\033[93m', # Yellow
            'DEFAULT': '\033[0m'     # Default
        }

    def wait_for_stack_completion(self, stack_name: str) -> bool:
        """Monitor stack events and wait for completion"""
        print("\n⏳ Waiting for stack operation to complete...\n")
        last_event_time = datetime.now(timezone.utc) - timedelta(seconds=10)
        
        while True:
            try:
                events = self.cf_client.describe_stack_events(
                    StackName=stack_name
                )['StackEvents']
                
                for event in reversed(events):
                    if event['Timestamp'] > last_event_time:
                        self._print_event(event)
                        last_event_time = event['Timestamp']
                
                stack = self.cf_client.describe_stacks(
                    StackName=stack_name
                )['Stacks'][0]
                status = stack['StackStatus']
                
                if not status.endswith('IN_PROGRESS'):
                    return self._handle_final_status(status)
                    
                time.sleep(5)
                
            except ClientError as e:
                print(f"❌ Error monitoring stack: {e}")
                return False
    
    def _print_event(self, event: Dict) -> None:
        """Print a formatted stack event"""
        status = event['ResourceStatus']
        resource_type = event['ResourceType']
        logical_id = event['LogicalResourceId']
        
        # Determine color
        color = self.colors['DEFAULT']
        for status_type, status_color in self.colors.items():
            if status_type in status:
                color = status_color
                break
        
        print(f"{color}{status}\033[0m - {resource_type} - {logical_id}")
        
        if 'ResourceStatusReason' in event:
            print(f"  Reason: {event['ResourceStatusReason']}")
    
    def _handle_final_status(self, status: str) -> bool:
        """Handle the final stack status"""
        if status.endswith('COMPLETE') and not status.endswith('ROLLBACK_COMPLETE'):
            print(f"\n✅ Stack operation completed successfully with status: {status}")
            return True
        else:
            print(f"\n❌ Stack operation failed with status: {status}")
            return False

class StackManager:
    """Manages CloudFormation stack operations"""
    
    def __init__(self, config: Dict[str, str]):
        self.config = config
        self.cf_client = boto3.client('cloudformation')
        self.monitor = StackMonitor(self.cf_client)

    def get_template_body(self) -> str:
        """Fetch the CloudFormation template"""
        try:
            response = requests.get(self.config['template_url'])
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching template: {e}")
            sys.exit(1)

    def stack_exists(self) -> bool:
        """Check if stack exists"""
        try:
            self.cf_client.describe_stacks(StackName=self.config['stack_name'])
            return True
        except ClientError as e:
            if 'does not exist' in str(e):
                return False
            raise e

    def create_or_update_stack(self) -> None:
        """Create or update the CloudFormation stack"""
        template_body = self.get_template_body()
        
        stack_params = {
            'StackName': self.config['stack_name'],
            'TemplateBody': template_body,
            'Capabilities': ['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM'],
            'Parameters': [
                {
                    'ParameterKey': 'MyAssetsBucketName',
                    'ParameterValue': self.config['bucket_name']
                },
                {
                    'ParameterKey': 'MyAssetsBucketPrefix',
                    'ParameterValue': self.config['bucket_prefix']
                }
            ]
        }

        try:
            if self.stack_exists():
                print(f"\n🔄 Updating stack: {self.config['stack_name']}")
                try:
                    self.cf_client.update_stack(**stack_params)
                    print("Stack update initiated...")
                except ClientError as e:
                    if 'No updates are to be performed' in str(e):
                        print("✨ No updates needed for the stack.")
                        return
                    raise e
            else:
                print(f"\n🆕 Creating new stack: {self.config['stack_name']}")
                self.cf_client.create_stack(**stack_params)
                print("Stack creation initiated...")

            if not self.monitor.wait_for_stack_completion(self.config['stack_name']):
                print("\n❌ Stack operation failed. Check CloudFormation console for details.")
                sys.exit(1)

        except ClientError as e:
            print(f"\n❌ Error during stack operation: {e}")
            sys.exit(1)

def main():
    """Main function"""
    print("\n🚀 CloudFormation Stack Manager\n")
    print("Press any key to continue or 'q' to quit...")
    
    if readchar.readchar().lower() == 'q':
        print("\nOperation cancelled by user")
        sys.exit(0)
    
    try:
        # Get configuration
        config = ConfigManager.get_user_config()
        
        # Initialize and run stack manager
        stack_manager = StackManager(config)
        stack_manager.create_or_update_stack()
        
    except Exception as e:
        print(f"\n❌ An unexpected error occurred: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()