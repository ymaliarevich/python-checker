from web3 import Web3
import json
import datetime

ETHEREUM_NODE_URL = "https://mainnet.infura.io/v3/64867581a7784b99b648be9f819ca3d8"  # ОБЯЗАТЕЛЬНО ЗАМЕНИТЕ НА ВАШ URL

UNISWAP_V2_ROUTER_ADDRESS = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"
ROUTER_ABI = json.loads(
    '[{"name":"getAmountsOut","inputs":[{"type":"uint256","name":"amountIn"},{"type":"address[]","name":"path"}],"outputs":[{"type":"uint256[]","name":"amounts"}],"stateMutability":"view","type":"function"}]')

TOKEN_ADDRESSES = {
    "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
    "USDC": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
    "DAI": "0x6B175474E89094C44Da98b954EedeAC495271d0F"
}

TOKEN_DECIMALS = {
    "USDT": 6,
    "USDC": 6,
    "DAI": 18
}


def get_uniswap_v2_price(w3_instance, router, token_in_sym, token_out_sym, amount_in_norm=1):
    try:
        token_in_addr = Web3.to_checksum_address(TOKEN_ADDRESSES[token_in_sym])
        token_out_addr = Web3.to_checksum_address(TOKEN_ADDRESSES[token_out_sym])
        token_in_dec = TOKEN_DECIMALS[token_in_sym]
        token_out_dec = TOKEN_DECIMALS[token_out_sym]

        amount_in_raw = int(amount_in_norm * (10 ** token_in_dec))
        path = [token_in_addr, token_out_addr]
        amounts_out_raw = router.functions.getAmountsOut(amount_in_raw, path).call()
        amount_out_normalized = amounts_out_raw[1] / (10 ** token_out_dec)
        return amount_out_normalized / amount_in_norm
    except Exception as e:
        print(f"Ошибка для {token_in_sym}/{token_out_sym}: {e}")
        return None


if __name__ == "__main__":
    if ETHEREUM_NODE_URL == "YOUR_ETHEREUM_NODE_URL" or not ETHEREUM_NODE_URL:
        print("Ошибка: ETHEREUM_NODE_URL не указан. Замените 'YOUR_ETHEREUM_NODE_URL' в скрипте.")
    else:
        try:
            w3 = Web3(Web3.HTTPProvider(ETHEREUM_NODE_URL))
            if not w3.is_connected():
                print(f"Не удалось подключиться к Ethereum Node: {ETHEREUM_NODE_URL}")
            else:
                print(f"Подключено к Ethereum. Текущий блок: {w3.eth.block_number}")
                uniswap_router_contract = w3.eth.contract(address=Web3.to_checksum_address(UNISWAP_V2_ROUTER_ADDRESS),
                                                          abi=ROUTER_ABI)

                print(f"\nЦены на Uniswap V2 ({datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}):\n")

                price_usdt_usdc = get_uniswap_v2_price(w3, uniswap_router_contract, "USDT", "USDC")
                if price_usdt_usdc is not None:
                    print(f"1 USDT = {price_usdt_usdc:.6f} USDC")

                price_usdt_dai = get_uniswap_v2_price(w3, uniswap_router_contract, "USDT", "DAI")
                if price_usdt_dai is not None:
                    print(f"1 USDT = {price_usdt_dai:.6f} DAI")

        except Exception as e:
            print(f"Общая ошибка выполнения: {e}")