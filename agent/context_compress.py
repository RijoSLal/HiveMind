from openai import OpenAI
import os 
import ryml # type: ignore
from typing import Union
import logging_setup
import logging
from dotenv import load_dotenv

logging_setup.setup_config()
logger = logging.getLogger(__name__)

load_dotenv()

class Compress_Context:
    """
    handles compressing chat context using an openai model and a system prompt loaded from a yaml file.
    """
    def __init__(self, file_path: str):
        """
        initialize the compress_context object.

        args:
            file_path (str): path to the yaml file containing the system prompt.

        sets:
            self.prompt (str): the system prompt loaded from the yaml file.
            self.client (OpenAI): the openai api client initialized with the api key from environment.
        """
        self.prompt = self.system_prompt(file_path)
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def context_compressor_async(self, context: Union[str, list], model: str, temp: int, max_tokens: int, timeout: float = 6.0):

        """
        compress the given context using the specified openai chat model.

        args:
            context (str | list): the chat context to compress. can be a string or a list of message dicts with 'role' and 'content'.
            model (str): the openai model to use for compression.
            temp (int): the temperature setting for the model.
            max_tokens (int): maximum number of tokens the response can contain.
            timeout (float, optional): request timeout in seconds. default is 10.0.

        returns:
            str | None: the compressed context returned by the model, or None if an error occurs.
        """

        if isinstance(context, list):
           context = self.process_context(context)

        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "system", "content": self.prompt},{"role": "user", "content": context}],
                timeout=timeout,
                temperature=temp, 
                max_tokens=max_tokens,
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"{model} failed : {e}")
            return 
        
    def process_context(self, context: list):

        """
        convert a list of chat turns into a single string.

        args:
            context (list): list of message dicts, each containing 'role' and 'content'.

        returns:
            str: concatenated chat turns in the format "role : content\n".
        """

        text = ""
        for turn in context:
            text+=f"{turn.get("role")} : {turn.get("content")}\n"
        logger.info("preprocessing completed")
        return text

    def system_prompt(self, file_path: str) -> str:

        """
        load the system prompt from a yaml file and convert it to a string.

        args:
            file_path (str): path to the yaml file containing the prompt under the 'prompt' key.

        returns:
            str: the system prompt as a decoded string.
        """

        with open(file_path, 'r') as f:
            yaml_content = f.read()

        tree = ryml.parse_in_arena(yaml_content)
        root = tree.root_id()
        prompt_node = tree.find_child(root, "prompt")

        prompt_mem = tree.val(prompt_node)  
        prompt = prompt_mem.tobytes().decode("utf-8")  
        return prompt
