from jupyter import execute_swap_solana


async def example_swap():
    from_token_mint = "So11111111111111111111111111111111111111112"
    to_token_mint = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    amount = 5_000
    result = await execute_swap_solana(from_token_mint, to_token_mint, amount)
    print(result)
