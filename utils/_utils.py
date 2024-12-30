import torch
import os
import functools


from .logging_utils import ColorFormatter
from .class_utils import ConversationHistory
from typing import Any
from datetime import datetime

from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    PreTrainedModel,
    BatchEncoding,
    PreTrainedTokenizer
)

def load_model(model_name:str,
               parallel:bool=False,
               device:str='cuda',
               dtype:str='b16',
) -> tuple[PreTrainedModel, PreTrainedTokenizer]:
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto" if parallel else device, 
        torch_dtype=torch.float32 if dtype == "f32" else torch.bfloat16,
    )
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    return model, tokenizer  # type: ignore

def generate(
    model: PreTrainedModel,
    inputs: BatchEncoding,
    tokenizer: PreTrainedTokenizer,
    max_new_tokens: int = 128,
) -> str:
    output = model.generate(
        inputs.input_ids,
        attention_mask=inputs.attention_mask,
        max_new_tokens=max_new_tokens,
        pad_token_id=tokenizer.eos_token_id,
    )
    return tokenizer.decode(
        output[0][len(inputs.input_ids[0]) :], skip_special_tokens=True
    )

# ==============================================================================================================
# Function decorators 
# ==============================================================================================================
def log_call(logger: Any):
    """
    Function decorator to log function calls with timestamp when DEBUG_MODE is enabled.
    """
    debug = os.environ.get('DEBUG_MODE', 'False').lower() in ['true', '1', 'yes']

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if debug:
                timestamp = datetime.now().isoformat()
                logger.debug(f"[{timestamp}] - Called: {func.__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator