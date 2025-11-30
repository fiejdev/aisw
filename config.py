import os
from openai import AzureOpenAI


def load_dotenv_file(path: str = ".env") -> None:
	if os.path.exists(path) and os.path.isfile(path):
		for line in open(path, "r", encoding="utf-8").read().splitlines():
			line = line.strip()
			if not line or line.startswith("#"):
				continue
			if "=" in line:
				key, value = line.split("=", 1)
				key = key.strip()
				value = value.strip().strip('"').strip("'")
				if key and value and key not in os.environ:
					os.environ[key] = value


def get_azure_openai_client() -> AzureOpenAI:
	return AzureOpenAI(
		api_key=os.environ["AZURE_OPENAI_API_KEY"],
		azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
		api_version=os.environ["AZURE_OPENAI_API_VERSION"],
	)


def get_azure_deployment() -> str:
	return os.environ["AZURE_OPENAI_DEPLOYMENT"]
