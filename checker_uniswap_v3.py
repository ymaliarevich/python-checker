from web3 import Web3
import json  # Понадобится, если будете загружать ABI из файлов

# --- Конфигурация ---
ETHEREUM_RPC_URL = "https://mainnet.infura.io/v3/64867581a7784b99b648be9f819ca3d8"  # !!! ЗАМЕНИТЕ НА ВАШ RPC URL !!!
UNISWAP_V3_QUOTER_V2_ADDRESS = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"

# Адреса токенов в Ethereum Mainnet
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

# Наиболее распространенная комиссия для пулов стейблкоин/стейблкоин (0.01%)
# Для USDT/USDC и USDT/DAI это обычно 100 (0.01%)
STABLECOIN_POOL_FEE = 100

# --- ABI (Application Binary Interfaces) ---
# Минимальный ABI для QuoterV2 (функция quoteExactInputSingle)
QUOTER_V2_ABI = json.loads("""
[
  {
    "inputs": [
      {
        "internalType": "address",
        "name": "tokenIn",
        "type": "address"
      },
      {
        "internalType": "address",
        "name": "tokenOut",
        "type": "address"
      },
      {
        "internalType": "uint24",
        "name": "fee",
        "type": "uint24"
      },
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      },
      {
        "internalType": "uint160",
        "name": "sqrtPriceLimitX96",
        "type": "uint160"
      }
    ],
    "name": "quoteExactInputSingle",
    "outputs": [
      {
        "internalType": "uint256",
        "name": "amountOut",
        "type": "uint256"
      }
    ],
    "stateMutability": "nonpayable",
    "type": "function"
  }
]
""")

# Минимальный ABI для ERC20 (функция decimals)
ERC20_ABI = json.loads("""
[
  {
    "inputs": [],
    "name": "decimals",
    "outputs": [
      {
        "internalType": "uint8",
        "name": "",
        "type": "uint8"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]
""")


def get_uniswap_v3_price(w3, token_in_address, token_out_address, fee, amount_in_human_readable=1):
    """
    Получает цену для пары токенов на Uniswap V3, котируя 1 единицу token_in.
    """
    quoter_contract = w3.eth.contract(address=UNISWAP_V3_QUOTER_V2_ADDRESS, abi=QUOTER_V2_ABI)

    token_in_contract = w3.eth.contract(address=token_in_address, abi=ERC20_ABI)
    token_out_contract = w3.eth.contract(address=token_out_address, abi=ERC20_ABI)

    try:
        token_in_decimals = token_in_contract.functions.decimals().call()
        token_out_decimals = token_out_contract.functions.decimals().call()
    except Exception as e:
        print(f"Ошибка при получении decimals для токенов: {e}")
        return None

    # Конвертируем 1 единицу token_in в его наименьшие единицы (wei-подобные)
    amount_in_wei = int(amount_in_human_readable * (10 ** token_in_decimals))

    try:
        # Котируем обмен
        # sqrtPriceLimitX96 = 0 означает отсутствие лимита цены при котировке
        amount_out_wei = quoter_contract.functions.quoteExactInputSingle(
            token_in_address,
            token_out_address,
            fee,
            amount_in_wei,
            0  # sqrtPriceLimitX96
        ).call()

        # Конвертируем полученное количество token_out обратно в человекочитаемый формат
        amount_out_human_readable = amount_out_wei / (10 ** token_out_decimals)
        return amount_out_human_readable

    except Exception as e:
        # Распространенная ошибка: если пул с такой комиссией не существует или недостаточно ликвидности.
        # Сообщение может содержать "Too little_liquidity" или быть более общим.
        print(f"Ошибка при котировке цены для {token_in_address}/{token_out_address} с комиссией {fee}: {e}")
        return None


if __name__ == "__main__":
    if ETHEREUM_RPC_URL == "YOUR_ETHEREUM_RPC_URL":
        print("ПОЖАЛУЙСТА, ЗАМЕНИТЕ 'YOUR_ETHEREUM_RPC_URL' в коде на ваш RPC URL!")
    else:
        w3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC_URL))

        if not w3.is_connected():
            print("Не удалось подключиться к узлу Ethereum. Проверьте ваш RPC URL.")
        else:
            print(f"Подключено к Ethereum ноде: {w3.is_connected()}")
            print(f"Номер последнего блока: {w3.eth.block_number}")
            print("-" * 30)

            # --- Получаем цену USDT/USDC (сколько USDC за 1 USDT) ---
            print("Запрашиваем цену USDT/USDC...")
            price_usdt_usdc = get_uniswap_v3_price(w3, USDT_ADDRESS, USDC_ADDRESS, STABLECOIN_POOL_FEE)
            if price_usdt_usdc is not None:
                print(f"1 USDT = {price_usdt_usdc:.6f} USDC (комиссия пула: {STABLECOIN_POOL_FEE / 10000}%)")
            else:
                print("Не удалось получить цену для USDT/USDC.")

            print("-" * 30)

            # --- Получаем цену USDT/DAI (сколько DAI за 1 USDT) ---
            print("Запрашиваем цену USDT/DAI...")
            price_usdt_dai = get_uniswap_v3_price(w3, USDT_ADDRESS, DAI_ADDRESS, STABLECOIN_POOL_FEE)
            if price_usdt_dai is not None:
                print(f"1 USDT = {price_usdt_dai:.6f} DAI (комиссия пула: {STABLECOIN_POOL_FEE / 10000}%)")
            else:
                print("Не удалось получить цену для USDT/DAI.")

            print("-" * 30)

            # --- Пример обратной котировки: USDC/USDT (сколько USDT за 1 USDC) ---
            # print("Запрашиваем цену USDC/USDT...")
            # price_usdc_usdt = get_uniswap_v3_price(w3, USDC_ADDRESS, USDT_ADDRESS, STABLECOIN_POOL_FEE)
            # if price_usdc_usdt is not None:
            #     print(f"1 USDC = {price_usdc_usdt:.6f} USDT (комиссия пула: {STABLECOIN_POOL_FEE/10000}%)")
            # else:
            #    print("Не удалось получить цену для USDC/USDT.")