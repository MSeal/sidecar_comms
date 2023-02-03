import os
import string
from typing import Optional

import openai
from IPython import get_ipython
from IPython.core.interactiveshell import InteractiveShell


def generate_prompt(prompt: str) -> str:
    # look up any mentioned variables in the user namespace
    # and add them to the prompt as a variable definition
    # e.g. if the prompt is "tell me about my_dataframe",
    # and my_dataframe is a pandas dataframe in the user namespace,
    # then the prompt will be:
    # "my_dataframe = pd.DataFrame(...)
    #  write a Markdown snippet for the following: tell me about my_dataframe"
    prompt = look_up_mentioned_variables(prompt)
    prompt = f"write a Markdown snippet for the following:\n{prompt}"
    return prompt


def generate_response(prompt: str, **kwargs) -> str:
    """Generate a response"""
    # Use your API key
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY environment variable not set")

    openai.api_key = key
    prompt_params = dict(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=0.95,
    )
    prompt_params.update(kwargs)

    # Generate text
    completions = openai.Completion.create(**prompt_params)
    return completions.choices[0].text


def look_up_mentioned_variables(
    prompt: str,
    ipython_shell: Optional[InteractiveShell] = None,
) -> str:
    ipython = ipython_shell or get_ipython()

    prompt_variables = {}
    # space separation for now, nothing fancy
    for item in prompt.split():
        if not item.startswith(tuple(string.ascii_letters)):
            # not a valid python identifier
            continue

        # remove any leading/trailing punctuation, but not valid syntax
        valid_suffixes = "().]_"
        invalid_suffixes = "".join([c for c in string.punctuation if c not in valid_suffixes])
        poss_var = item.rstrip(invalid_suffixes)

        if poss_var in ipython.user_ns:
            # variable is already in the user namespace
            var = ipython.user_ns[poss_var]
            prompt_variables[poss_var] = var
        else:
            # variable is not in the user namespace
            prompt_variables[poss_var] = None

    safe_prompt_variables = {}
    for poss_var, var in prompt_variables.items():
        forbidden = ["os.", "sys.", "openai.", "ipython.", "get_ipython"]
        if poss_var.startswith(tuple(forbidden)):
            # don't want to evaluate any of these
            continue

        if var is None:
            # maybe there's a reference to an attribute or method that needs to be evaluated
            try:
                var = eval(poss_var)
                safe_prompt_variables[poss_var] = var
                var_type = repr(type(var))
                safe_prompt_variables[f"{poss_var} type"] = var_type
            except Exception:
                var = None

        if var is not None:
            var_type = repr(type(var))
            safe_prompt_variables[f"{poss_var} type"] = var_type

            if "pandas.core" in var_type:
                # special dataframe handling since we don't want to send OpenAI the entire dataframe
                # due to a 4097 token limit
                safe_prompt_variables[f"{poss_var} shape"] = var.shape
                safe_prompt_variables[f"{poss_var} head"] = var.head(1)
                safe_prompt_variables[f"{poss_var} tail"] = var.tail(1)
                # prompt_variables[f"{poss_var} description"] = var.describe()
                if "DataFrame" in var_type:
                    safe_prompt_variables[f"{poss_var} columns"] = list(var.columns)
            else:
                safe_prompt_variables[poss_var] = var

    if not safe_prompt_variables:
        return prompt

    # add the variable definitions to the prompt
    var_defs = "\n".join([f"{k}={v}" for k, v in safe_prompt_variables.items()])
    return f"{var_defs}\n\n{prompt}"
