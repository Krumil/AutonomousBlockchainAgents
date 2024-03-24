from web3 import Web3
import dotenv
import json
import os
import random
import requests

dotenv.load_dotenv()


def get_possible_chains():
    return ["arbitrum", "base", "optimism", "polygon_zk", "scroll", "zksync_era"]


def get_chain_key(chain_name):
    chain_name = chain_name.lower()
    lifi_chains = json.load(open("lifi-chains.json"))
    for chain in lifi_chains:
        if chain["name"].lower() == chain_name:
            return chain["key"]


def get_chain_id(chain_name):
    chain_name = chain_name.lower()
    lifi_chains = json.load(open("lifi-chains.json"))
    for chain in lifi_chains:
        if chain["name"].lower() == chain_name:
            return chain["id"]


def convert_eth_to_wei(amount_eth):
    return Web3.to_wei(amount_eth, "ether")


def convert_wei_to_eth(amount_wei):
    return Web3.from_wei(amount_wei, "ether")


def count_accounts():
    count = 0
    while True:
        address_key = f"ADDRESS_{count + 1}"
        private_key = f"PRIVATE_KEY_{count + 1}"
        if os.getenv(address_key) and os.getenv(private_key):
            count += 1
        else:
            break
    return count


def get_accounts_from_env():
    num_accounts = count_accounts()
    accounts = [
        {
            "address": os.getenv(f"ADDRESS_{i+1}"),
            "private_key": os.getenv(f"PRIVATE_KEY_{i+1}"),
        }
        for i in range(num_accounts)
    ]
    return accounts


def get_accounts_from_file():
    with open("wallets.json", "r") as file:
        return json.load(file)


def load_files():
    hNFT_addresses = json.load(open("hNFT-addresses.json"))
    hFT_addresses = json.load(open("hFT-addresses.json"))
    domains = json.load(open("domains.json"))
    hNFT_abi = json.load(open("abi/hNFT-abi.json"))
    hFT_abi = json.load(open("abi/hFT-abi.json"))
    erc20_abi = json.load(open("abi/lifi-erc20-abi.json"))
    lifi_chains = json.load(open("lifi-chains.json"))

    networks = get_possible_chains()
    alchemy_url_list = {chain: os.getenv(f"{chain.upper()}_URL") for chain in networks}

    return (
        hNFT_addresses,
        hFT_addresses,
        domains,
        alchemy_url_list,
        hNFT_abi,
        hFT_abi,
        erc20_abi,
        lifi_chains,
    )


# Initialize web3 with Alchemy provider
def init_web3(provider_url):
    return Web3(Web3.HTTPProvider(provider_url))


# Function to read ABI from a local file
def load_abi(file_path):
    with open(file_path, "r") as file:
        return json.load(file)


def estimate_gas_price(web3):
    gas_price = web3.eth.gas_price
    return gas_price


def get_token_info(chain, symbol):
    url = "https://li.quest/v1/token"
    headers = {"accept": "application/json"}
    response = requests.get(
        url, headers=headers, params={"chain": chain, "token": symbol}
    )
    return response.json()


def get_token_balance(chain_name, account_address, token_symbol):
    _, _, _, alchemy_url_list, _, _, erc20_abi, _ = load_files()

    alchemy_url = alchemy_url_list.get(chain_name)
    if not alchemy_url:
        raise ValueError(f"Alchemy URL for chain {chain_name} not found.")

    web3 = init_web3(alchemy_url)
    if token_symbol == "ETH":
        balance = web3.eth.get_balance(Web3.to_checksum_address(account_address))
        return balance

    token_info = get_token_info(get_chain_id(chain_name), token_symbol)
    token_address = token_info["address"]

    token_contract = web3.eth.contract(
        address=Web3.to_checksum_address(token_address), abi=erc20_abi
    )
    balance = token_contract.functions.balanceOf(
        Web3.to_checksum_address(account_address)
    ).call()
    return balance
