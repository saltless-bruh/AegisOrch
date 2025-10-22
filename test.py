from daytona import Daytona, DaytonaConfig

# Define the configuration
config = DaytonaConfig(api_key="dtn_1e50f8e8e887bc6d6fde132eec628b4d1798c15d8d44215ca8ead4913bf44699")

# Initialize the Daytona client
daytona = Daytona(config)

# Create the Sandbox instance
sandbox = daytona.create()

# Run the code securely inside the Sandbox
response = sandbox.process.code_run('print("Hello World from code!")')
if response.exit_code != 0:
    print(f"Error: {response.exit_code} {response.result}")
else:
    print(response.result)
