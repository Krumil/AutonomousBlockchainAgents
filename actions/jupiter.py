import base58
import base64
import json
import os
import time

from solders import message
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solders.transaction import VersionedTransaction

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Processed
from solana.rpc.types import TxOpts

from helius import BalancesAPI

from jupiter_python_sdk.jupiter import Jupiter

SOLANA_RPC_ENDPOINT_URL = (
    f"https://mainnet.helius-rpc.com/?api-key={os.getenv('HELIOUS_API_KEY')}"
)
balances_api = BalancesAPI(os.getenv("HELIOUS_API_KEY"))
private_key_string = os.getenv("SOLANA_PRIVATE_KEY_1")
private_key_bytes = base58.b58decode(private_key_string)
private_key = Keypair.from_bytes(private_key_bytes)

async_client = AsyncClient(SOLANA_RPC_ENDPOINT_URL)
jupiter = Jupiter(
    async_client=async_client,
    keypair=private_key,
)


async def get_quote_solana(from_token_mint, to_token_mint, amount, slippage=15):
    try:
        quote = await jupiter.quote(
            input_mint=from_token_mint,
            output_mint=to_token_mint,
            amount=amount,
            slippage_bps=slippage,
        )
    except Exception as e:
        quote = {
            "outAmount": 0,
        }
    finally:
        return quote


async def execute_swap_solana(
    from_token_mint, to_token_mint, amount, slippage=1, max_retries=3, retry_delay=5
):
    """
    Executes a swap with retry logic.

    Parameters are the same as before, with two new ones:
    - max_retries: int, the maximum number of retries upon failure.
    - retry_delay: int, delay between retries in seconds.
    """
    attempt = 0
    amount = int(amount)
    while attempt < max_retries:
        try:
            quote = await jupiter.quote(
                input_mint=from_token_mint,
                output_mint=to_token_mint,
                amount=amount,
                slippage_bps=slippage,
            )

            if quote:
                transaction_data = await jupiter.swap(
                    input_mint=from_token_mint,
                    output_mint=to_token_mint,
                    amount=amount,
                    slippage_bps=slippage,
                )

                raw_transaction = VersionedTransaction.from_bytes(
                    base64.b64decode(transaction_data)
                )
                signature = private_key.sign_message(
                    message.to_bytes_versioned(raw_transaction.message)
                )
                signed_txn = VersionedTransaction.populate(
                    raw_transaction.message, [signature]
                )
                opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
                result = await async_client.send_raw_transaction(
                    txn=bytes(signed_txn), opts=opts
                )
                transaction_id = json.loads(result.to_json())["result"]
                # print(
                #     f"Transaction sent: https://explorer.solana.com/tx/{transaction_id}"
                # )
                return f"Transaction between {from_token_mint} and {to_token_mint} executed successfully. Sent {amount} {from_token_mint} with id https://explorer.solana.com/tx/{transaction_id}"
            else:
                raise Exception("No suitable quote found.")
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            attempt += 1
            if attempt < max_retries:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                return "All retries exhausted. Transaction failed."


# def get_tokens_name_list():
#     tokens = asyncio.run(get_tokens_name_string())
#     return tokens


async def get_tokens_name_string():
    token_list = await jupiter.get_tokens_list()
    return ", ".join([token["name"] for token in token_list])


async def get_token_info_by_name_or_symbol(token_name_or_symbol):
    token_list = await jupiter.get_tokens_list(list_type="all")
    for token in token_list:
        # lowercase both token and token["name"] to make it case insensitive
        token_name_or_symbol = token_name_or_symbol.lower()
        token_name_or_symbol = token_name_or_symbol.replace(" ", "")
        if (
            token["name"].lower() == token_name_or_symbol
            or token["symbol"].lower() == token_name_or_symbol
        ):
            return token
    return None


async def get_assets_by_owner(wallet_address):
    assets = balances_api.get_balances(wallet_address)
    tokens = assets["tokens"]
    tokens = [token for token in tokens if token["amount"] > 0]
    tokens = [{"mint": token["mint"], "amount": token["amount"]} for token in tokens]

    # add sol to tokens from assets.native_balance
    native_balance = assets["nativeBalance"]
    tokens.append(
        {
            "mint": "So11111111111111111111111111111111111111112",
            "amount": native_balance,
        }
    )

    return tokens


async def get_supported_jupiter_tokens(wallet_address):
    jupiter_token_list = await jupiter.get_tokens_list(list_type="all")
    wallet_tokens = await get_assets_by_owner(wallet_address=wallet_address)

    supported_tokens = []
    for jupiter_token in jupiter_token_list:
        for wallet_token in wallet_tokens:
            if wallet_token["mint"] == jupiter_token["address"]:
                wallet_token.update(jupiter_token)
                supported_tokens.append(wallet_token)

    return supported_tokens


async def get_wallet_balance():
    wallet_address = os.getenv("SOLANA_ADDRESS_1")
    tokens = await get_supported_jupiter_tokens(wallet_address=wallet_address)
    return json.dumps(tokens)


async def get_wallet_balance_with_solana_values():
    tokens = await get_wallet_balance()
    tokens = json.loads(tokens)
    for token in tokens:
        if token["mint"] == "So11111111111111111111111111111111111111112":
            token["solValue"] = token["amount"] / 1000000000
        else:
            # get quote for token
            quote = await get_quote_solana(
                token["mint"],
                "So11111111111111111111111111111111111111112",
                token["amount"],
            )
            token["solValue"] = int(quote["outAmount"]) / 1000000000
    return json.dumps(tokens)


async def get_wallet_sol_value():
    tokens = await get_wallet_balance_with_solana_values()
    tokens = json.loads(tokens)
    sol_value = 0
    for token in tokens:
        sol_value += token["solValue"]
    return sol_value


# def get_token_info_by_name_or_symbol_async(token_name_or_symbol):
#     token = asyncio.run(get_token_info_by_name_or_symbol(token_name_or_symbol))
#     return token


# def execute_swap_solana_async(from_token_mint, to_token_mint, amount):
#     result = asyncio.run(execute_swap_solana(from_token_mint, to_token_mint, amount))
#     return result


# # if main
# if __name__ == "__main__":
#     result = asyncio.run(
#         execute_swap_solana(
#             from_token_mint="3U8cZTbq4QkT14Kvb8Rj8CxfcyQx5V2XJHicMYE7QDmQ",
#             to_token_mint="HZ32SiTtw3kYyaHTtTfpHVF8EyXFcy7MBQXeFpnNvQ9c",
#             amount=109322994,
#         )
#     )
#     print(result)
