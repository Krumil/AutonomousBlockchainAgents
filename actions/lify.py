import requests
import time
from utils import (
    load_files,
    init_web3,
    get_chain_key,
    get_chain_id,
    convert_eth_to_wei,
    get_token_balance,
    get_accounts_from_env,
)

# Load necessary data
_, _, _, alchemy_url_list, _, _, erc20_abi, lifi_chains = load_files()


def get_tokens():
    optional_filter = ["BASE"]  # Both numeric and mnemonic can be used
    optional_chain_types = "EVM"  # By default, only EVM tokens will be returned

    response = requests.get(
        "https://li.quest/v1/tokens",
        params={
            "chains": ",".join(map(str, optional_filter)),
            "chainTypes": optional_chain_types,
        },
    )
    return response.json()


def get_quote(
    starting_chain, destination_chain, from_token, to_token, from_amount, from_address
):
    starting_domain = get_chain_key(starting_chain)
    destination_domain = get_chain_key(destination_chain)
    url = "https://li.quest/v1/quote"
    params = {
        "fromChain": starting_domain,
        "toChain": destination_domain,
        "fromToken": from_token,
        "toToken": to_token,
        "fromAmount": from_amount,
        "fromAddress": from_address,
    }
    response = requests.get(url, params=params)
    return response.json()


def get_transaction_status(bridge, starting_chain, destination_chain, tx_hash):
    starting_domain = get_chain_key(starting_chain)
    destination_domain = get_chain_key(destination_chain)
    url = "https://li.quest/v1/status"
    params = {
        "bridge": bridge,
        "fromChain": starting_domain,
        "toChain": destination_domain,
        "txHash": tx_hash,
    }
    response = requests.get(url, params=params)
    return response.json()


def check_and_set_allowance(
    web3,
    chain,
    account_address,
    private_key,
    token_address,
    approval_address,
    amount,
    abi,
):
    zero_address = "0x0000000000000000000000000000000000000000"
    if token_address == zero_address:
        return

    contract = web3.eth.contract(address=token_address, abi=abi)
    current_allowance = contract.functions.allowance(
        account_address, approval_address
    ).call()

    if current_allowance < amount:
        amount_remaining = amount - current_allowance
        chain_id = get_chain_id(chain)
        nonce = web3.eth.get_transaction_count(account_address)
        approve_tx = contract.functions.approve(
            approval_address, amount_remaining
        ).build_transaction(
            {
                "from": account_address,
                "chainId": chain_id,
                "nonce": nonce,
            }
        )
        signed_tx = web3.eth.account.sign_transaction(approve_tx, private_key)
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        web3.eth.wait_for_transaction_receipt(tx_hash)


def execute_swap(
    starting_chain,
    destination_chain,
    from_token,
    to_token,
    from_amount,
    account_address,
    private_key,
):
    alchemy_url = alchemy_url_list[starting_chain]
    web3 = init_web3(alchemy_url)
    quote = get_quote(
        starting_chain,
        destination_chain,
        from_token,
        to_token,
        from_amount,
        account_address,
    )
    check_and_set_allowance(
        web3,
        starting_chain,
        account_address,
        private_key,
        quote["action"]["fromToken"]["address"],
        quote["estimate"]["approvalAddress"],
        from_amount,
        erc20_abi,
    )

    nonce = web3.eth.get_transaction_count(account_address)

    tx = {
        "from": quote["transactionRequest"]["from"],
        "to": quote["transactionRequest"]["to"],
        "value": quote["transactionRequest"]["value"],  # Convert hex to int
        "data": quote["transactionRequest"]["data"],
        "gas": quote["transactionRequest"]["gasLimit"],
        "gasPrice": quote["transactionRequest"]["gasPrice"],
        "nonce": nonce,
        "chainId": get_chain_id(starting_chain),
    }
    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    print(f"Transaction hash: {tx_hash.hex()}")
    result = wait_for_transaction_done(tx_hash.hex())
    if result:
        return receipt
    else:
        raise Exception(
            "Transaction failed: "
            + tx_hash.hex()
            + ". Swapping "
            + from_token
            + " to "
            + to_token
            + " on "
            + starting_chain
            + " to "
            + destination_chain
            + " failed."
        )


def split_send_eth(
    starting_chain,
    destination_chains,
    from_token,
    to_token,
    from_amount,
    account_address,
    private_key,
):
    split_amount = convert_eth_to_wei(from_amount / len(destination_chains))

    for chain in destination_chains:
        execute_swap(
            starting_chain,
            chain,
            from_token,
            to_token,
            split_amount,
            account_address,
            private_key,
        )


# create a function to execute the swap within the same chain (e.g. Ethereum to Ethereum) with ETH as the from token and USDC as the to token
def execute_swap_ETH_to_USDC(chain, account_address, private_key, amount):
    receipt = execute_swap(
        chain, chain, "ETH", "USDC", amount, account_address, private_key
    )
    return receipt


def execute_swap_all_USDC_to_ETH(chain, account_address, private_key):
    amount = get_token_balance(chain, account_address, "USDC")
    if amount == 0:
        return
    receipt = execute_swap(
        chain, chain, "USDC", "ETH", amount, account_address, private_key
    )
    return receipt


def execute_swap_on_same_chain(from_token, to_token, from_amount):
    chain = "BASE"
    accounts = get_accounts_from_env()
    account_address = accounts[0]["address"]
    private_key = accounts[0]["private_key"]
    from_amount = convert_eth_to_wei(from_amount)
    receipt = execute_swap(
        chain, chain, from_token, to_token, from_amount, account_address, private_key
    )
    return receipt


def get_transaction_status(tx_hash):
    url = "https://li.quest/v1/status"
    params = {"txHash": tx_hash}
    response = requests.get(url, params=params)
    return response.json()


def wait_for_transaction_done(tx_hash):
    while True:
        try:
            status_result = get_transaction_status(tx_hash)
            if status_result["status"] == "DONE":
                print("Transaction completed successfully.")
                return True
            elif status_result["status"] == "FAILED":
                print("Transaction failed.")
                return False
            else:
                print(
                    f"Transaction status: {status_result['status']}. Waiting for completion..."
                )
                time.sleep(3)  # Adjusted to wait for 3 seconds as per the comment
        except Exception as e:
            print(f"An error occurred: {e}. Retrying...")
            time.sleep(3)  # wait for 3 seconds before retrying
