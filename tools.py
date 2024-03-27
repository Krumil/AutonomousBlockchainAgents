from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import StructuredTool, Tool
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from actions.lify import execute_swap_on_same_chain
from actions.jupiter import (
    execute_swap_solana,
    get_wallet_balance_with_solana_values,
    get_wallet_sol_value,
    get_token_info_by_name_or_symbol,
)
from actions.vision import call_vision_model_on_dexscreener, navigate_url


class ExecuteSwapInput(BaseModel):
    from_token_mint: str = Field(description="The address of the token to be swapped")
    to_token_mint: str = Field(description="The address of the token to be received")
    amount: float = Field(
        description="The amount of `from_token` to swap, in its smallest unit"
    )


execute_swap_tool = StructuredTool.from_function(
    coroutine=execute_swap_solana,
    name="ExecuteSwap",
    description="Executes a token swap between two tokens on the same chain",
    args_schema=ExecuteSwapInput,
)


class GetTokenInfoInput(BaseModel):
    token_name_or_symbol: str = Field(
        description="The symbol or the name of the token to get information about"
    )


get_token_info_tool = StructuredTool.from_function(
    coroutine=get_token_info_by_name_or_symbol,
    name="GetTokenInfo",
    description="Get information about a token on Solana",
    args_schema=GetTokenInfoInput,
)

# get_tokens_list_tool = StructuredTool.from_function(
#     func=get_tokens_list,
#     name="GetTokensList",
#     description="Get a list of available tokens on Solana",
# )

get_wallet_balance_tool = StructuredTool.from_function(
    coroutine=get_wallet_balance_with_solana_values,
    name="GetWalletBalance",
    description="Get the balance of your wallet on Solana",
)


get_wallet_balance_in_sol_values_tool = StructuredTool.from_function(
    coroutine=get_wallet_sol_value,
    name="GetSOLWalletBalance",
    description="Get the balance of your wallet in SOL value",
)


navigate_url_tool = StructuredTool.from_function(
    name="NavigateURL",
    func=navigate_url,
    description="Tool to navigate to a URL and extract information from the page",
)

trending_coins_tool = StructuredTool.from_function(
    name="GetTrendingCoinsSolana",
    func=call_vision_model_on_dexscreener,
    description="Get the current trending coin on Solana",
)
