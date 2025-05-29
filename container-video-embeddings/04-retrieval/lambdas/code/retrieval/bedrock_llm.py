from typing import List, Dict
from botocore.config import Config
import boto3

DEFAULT_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0"
#DEFAULT_MODEL_ID = "us.anthropic.claude-3-5-haiku-20241022-v1:0"

config = Config(
   retries = {
      'max_attempts': 10,
      'mode': 'adaptive'
   }
)


class ThinkingLLM:
    def __init__(
        self,
        model_id = None,
        budget_tokens = 0,
        max_tokens = 1024,
        system_prompt = None
    ):

        self.model_id = model_id if model_id else DEFAULT_MODEL_ID
        self.budget_tokens = budget_tokens
        self.max_tokens = max_tokens
        self.thinking_enabled = True if budget_tokens else False
        self.conversation: List[Dict] = []
        self.system_prompt = system_prompt
        self.reasoning_config = {"thinking": {"type": "enabled", "budget_tokens": self.budget_tokens}}

        # Initialize Bedrock client
        self.client = boto3.client(service_name="bedrock-runtime", config=config)

    def answer(self, content) -> str:
        """Get completion from Claude model based on conversation history.

        Returns:
            str: Model completion text
        """

        # Invoke model

        kwargs = dict(
            modelId=self.model_id,
            inferenceConfig=dict(maxTokens=self.max_tokens),
            messages=[
                {
                    "role": "user",
                    "content": content,
                }
            ],


        )
        if self.thinking_enabled:
            kwargs["additionalModelRequestFields"]=self.reasoning_config
        if self.system_prompt:
            kwargs["system"] = [{"text": self.system_prompt}]



        response = self.client.converse(**kwargs)
        # answer = response["output"]["message"]["content"][1]["text"]
        # reasoning = response["output"]["message"]["content"][0]["reasoningContent"]["reasoningText"]["text"]
        return response.get("output",{}).get("message",{}).get("content", [])
        
