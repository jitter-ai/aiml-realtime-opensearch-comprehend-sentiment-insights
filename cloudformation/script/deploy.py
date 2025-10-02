#!/usr/bin/env python3
import os
import subprocess
import sys
import json
from pathlib import Path
from botocore.exceptions import ClientError
import time
import boto3
from pydantic import BaseModel, Dict, List
from typing import Dict, List

class AssetInfo(BaseModel):
    """Model for asset information"""
    local_path: str
    s3_key: str

class LambdaAssets(BaseModel):
    """Model for Lambda assets"""
    lambda_function: AssetInfo
    lambda_layers: Dict[str, AssetInfo]

class DeploymentConfig(BaseModel):
    """Pydantic model for deployment configuration"""
    aws: Dict[str, str]
    assets: LambdaAssets
    template_path: str
    stack_parameters: List[Dict[str, str]]
    stack_capabilities: List[str]
    waiter_config: Dict[str, int]

    @classmethod
    def from_json(cls, data: dict):
        """Create instance from JSON data with proper structure"""
        # Restructure assets if needed
        if "assets" in data:
            assets = data["assets"]
            if "lambda_function" in assets and isinstance(assets["lambda_function"], dict):
                lambda_function = AssetInfo(**assets["lambda_function"])
                lambda_layers = {
                    name: AssetInfo(**layer_info)
                    for name, layer_info in assets.get("lambda_layers", {}).items()
                }
                data["assets"] = {"lambda_function": lambda_function, "lambda_layers": lambda_layers}
        
        return cls.model_validate(data)

@error_handler
def load_config() -> DeploymentConfig:
    """Load and validate deployment configuration"""
    config_path = Path(__file__).parent.parent / "config" / "deployment_config.json"
    logger.debug(f"Loading config from: {config_path}")
    with open(config_path, 'r') as f:
        return DeploymentConfig.from_json(json.load(f))

# Global configuration from JSON
CONFIG = load_config()
AWS_REGION = CONFIG['aws']['region']
STACK_NAME = CONFIG['aws']['stack_name']
ASSETS = CONFIG['assets']
TEMPLATE_PATH = CONFIG['template_path']
STACK_PARAMETERS = CONFIG['stack_parameters']
STACK_CAPABILITIES = CONFIG['stack_capabilities']
WAITER_CONFIG = CONFIG['waiter_config']

def get_aws_profiles():
    """Get list of available AWS profiles"""
    try:
        result = subprocess.run(['aws', 'configure', 'list-profiles'], 
                              capture_output=True, text=True, check=True)
        profiles = result.stdout.strip().split('\n')
        return [p for p in profiles if p]
    except subprocess.CalledProcessError:
        return []

class SessionManager:
    """Handles AWS session creation"""
    def __init__(self, region=AWS_REGION):
        self.session = None
        self.region = region
        self.setup_session()

    def setup_session(self):
        """Set up AWS session with selected profile"""
        profiles = get_aws_profiles()
        
        if not profiles:
            print("❌ No AWS profiles found.")
            print("💡 Tip: Configure your AWS credentials first:")
            print("    1. Run: aws configure")
            print("    2. Or set up SSO: aws configure sso")
            sys.exit(1)

        print("\n📋 Available AWS Profiles:")
        for idx, profile in enumerate(profiles, 1):
            print(f"[{idx}] {profile}", end='  ')
        print("\n")
        
        while True:
            try:
                choice = int(input("Select profile number: "))
                if 1 <= choice <= len(profiles):
                    selected_profile = profiles[choice - 1]
                    break
                print("Invalid selection. Please try again.")
            except ValueError:
                print("Please enter a valid number.")

        try:
            print(f"\n🔄 Creating session with profile: {selected_profile}")
            self.session = boto3.Session(profile_name=selected_profile, region_name=self.region)
            
            # Test the session
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            print(f"✅ Successfully authenticated with profile: {selected_profile}")
            print(f"✅ Account: {identity['Account']}")
            print(f"✅ User: {identity['Arn']}\n")
            
        except Exception as e:
            print(f"\n❌ Session initialization failed: {str(e)}")
            print("\n💡 Tips:")
            print("   1. Check your AWS credentials")
            print("   2. Verify your SSO configuration")
            print("   3. Check your internet connection")
            sys.exit(1)

class AssetManager:
    """Handles the bootstrap S3 bucket and asset uploads"""
    def __init__(self, session):
        self.session = session
        self.s3 = session.client('s3')
        self.account_id = session.client('sts').get_caller_identity()["Account"]
        self.region = session.region_name
        self.bucket_name = f"aos-artifacts-{self.account_id}-{self.region}"

    def ensure_bootstrap_bucket(self):
        """Create or verify existence of the bootstrap S3 bucket"""
        print(f"📦 Checking bootstrap bucket {self.bucket_name}...")
        try:
            self.s3.head_bucket(Bucket=self.bucket_name)
            print(f"✅ Bucket {self.bucket_name} already exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                try:
                    if self.region == "us-east-1":
                        self.s3.create_bucket(Bucket=self.bucket_name)
                    else:
                        self.s3.create_bucket(
                            Bucket=self.bucket_name,
                            CreateBucketConfiguration={'LocationConstraint': self.region}
                        )
                    print(f"✅ Successfully created bucket {self.bucket_name}")
                    return True
                except Exception as create_error:
                    print(f"❌ Failed to create bucket: {str(create_error)}")
                    return False
            else:
                print(f"❌ Error accessing bucket: {str(e)}")
                return False

    def upload_deployment_assets(self):
        """Upload Lambda function and layer zip files to S3"""
        print("\n📤 Uploading deployment assets...")
        for asset_type, assets in ASSETS.items():
            if isinstance(assets, dict):
                for asset_name, asset_info in assets.items():
                    self._upload_asset(asset_info['local_path'], asset_info['s3_key'])
            else:
                self._upload_asset(assets['local_path'], assets['s3_key'])
        print("✅ All assets uploaded successfully")

    def _upload_asset(self, local_path, s3_key):
        """Helper method to upload a single asset"""
        try:
            print(f"  ⏳ Uploading {local_path} to s3://{self.bucket_name}/{s3_key}...")
            self.s3.upload_file(local_path, self.bucket_name, s3_key)
            print(f"  ✅ Uploaded {s3_key}")
        except Exception as e:
            print(f"  ❌ Failed to upload {s3_key}: {str(e)}")
            raise

class StackDeployer:
    """Handles CloudFormation stack deployment"""
    def __init__(self, session, stack_name=STACK_NAME):
        self.session = session
        self.cf = session.client('cloudformation')
        self.stack_name = stack_name

    def _get_template_body(self):
        """Read CloudFormation template file"""
        with open(TEMPLATE_PATH, 'r') as f:
            return f.read()

    def _get_stack_parameters(self):
        """Get stack parameters including dynamic bucket name"""
        params = STACK_PARAMETERS.copy()
        params.append({
            'ParameterKey': 'MyAssetsBucketName',
            'ParameterValue': self.asset_manager.bucket_name
        })
        return params

    def deploy_stack(self):
        """Deploy or update CloudFormation stack"""
        try:
            self.create_stack()
        except ClientError as e:
            if e.response['Error']['Code'] == 'AlreadyExistsException':
                self.update_stack()
            else:
                raise

    def create_stack(self):
        """Create new CloudFormation stack"""
        print("Creating new stack...")
        self.cf.create_stack(
            StackName=self.stack_name,
            TemplateBody=self._get_template_body(),
            Capabilities=STACK_CAPABILITIES,
            Parameters=self._get_stack_parameters()
        )
        print("Waiting for stack creation to complete...")
        waiter = self.cf.get_waiter('stack_create_complete')
        waiter.wait(StackName=self.stack_name, WaiterConfig=WAITER_CONFIG)

    def update_stack(self):
        """Update existing CloudFormation stack"""
        print("Updating existing stack...")
        try:
            self.cf.update_stack(
                StackName=self.stack_name,
                TemplateBody=self._get_template_body(),
                Capabilities=STACK_CAPABILITIES,
                Parameters=self._get_stack_parameters()
            )
            print("Waiting for stack update to complete...")
            waiter = self.cf.get_waiter('stack_update_complete')
            waiter.wait(StackName=self.stack_name, WaiterConfig=WAITER_CONFIG)
        except ClientError as e:
            if 'No updates are to be performed' in str(e):
                print("No updates needed")
            else:
                raise

def main():
    try:
        print("\n🚀 AWS CloudFormation Deployment Tool\n")
        
        # Initialize session manager and get session with assumed role
        session_mgr = SessionManager()
        deployment_session = session_mgr.session

        # Initialize and run deployment
        asset_manager = AssetManager(session=deployment_session)
        stack_deployer = StackDeployer(asset_manager)

        asset_manager.ensure_bootstrap_bucket()
        asset_manager.upload_deployment_assets()
        stack_deployer.deploy_stack()

        print("✅ Deployment completed successfully!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()





