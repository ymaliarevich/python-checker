from web3 import Web3

# --- Конфигурация ---
INFURA_URL = "https://mainnet.infura.io/v3/64867581a7784b99b648be9f819ca3d8"
SUSHISWAP_ROUTER_ADDRESS = "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F"
SUSHISWAP_ROUTER_ABI = """
[
  {
    "inputs": [
      {
        "internalType": "uint256",
        "name": "amountIn",
        "type": "uint256"
      },
      {
        "internalType": "address[]",
        "name": "path",
        "type": "address[]"
      }
    ],
    "name": "getAmountsOut",
    "outputs": [
      {
        "internalType": "uint256[]",
        "name": "amounts",
        "type": "uint256[]"
      }
    ],
    "stateMutability": "view",
    "type": "function"
  }
]
"""

# Адреса токенов
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

# Десятичные знаки токенов
USDT_DECIMALS = 6
USDC_DECIMALS = 6
DAI_DECIMALS = 18

# --- Инициализация Web3 ---
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

if not w3.is_connected():
    print("Ошибка: Не удалось подключиться к узлу Ethereum.")
    exit()

# --- Инициализация контракта SushiSwap Router ---
sushiswap_router = w3.eth.contract(address=SUSHISWAP_ROUTER_ADDRESS, abi=SUSHISWAP_ROUTER_ABI)

def get_price(token_in_address, token_out_address, token_in_decimals, token_out_decimals, amount_in=1):
    """
    Получает цену одного токена (token_in) в другом токене (token_out).

    :param token_in_address: Адрес входного токена
    :param token_out_address: Адрес выходного токена
    :param token_in_decimals: Количество десятичных знаков для входного токена
    :param token_out_decimals: Количество десятичных знаков для выходного токена
    :param amount_in: Количество входного токена (по умолчанию 1)
    :return: Цена или None в случае ошибки
    """
    try:
        # Конвертируем количество входного токена в его наименьшие единицы (wei-like)
        amount_in_wei = int(amount_in * (10**token_in_decimals))

        # Путь обмена: token_in -> token_out
        path = [w3.to_checksum_address(token_in_address), w3.to_checksum_address(token_out_address)]

        # Вызов функции getAmountsOut
        amounts_out = sushiswap_router.functions.getAmountsOut(amount_in_wei, path).call()

        # Конвертируем результат обратно из наименьших единиц
        amount_out_adjusted = amounts_out[1] / (10**token_out_decimals)
        return amount_out_adjusted
    except Exception as e:
        print(f"Ошибка при получении цены для {token_in_address} -> {token_out_address}: {e}")
        return None

# --- Получение цен ---

print("Получение цен с SushiSwap...\n")

# 1. USDT/USDC
price_usdt_usdc = get_price(USDT_ADDRESS, USDC_ADDRESS, USDT_DECIMALS, USDC_DECIMALS)
if price_usdt_usdc is not None:
    print(f"1 USDT = {price_usdt_usdc:.6f} USDC")

# 2. USDT/DAI
price_usdt_dai = get_price(USDT_ADDRESS, DAI_ADDRESS, USDT_DECIMALS, DAI_DECIMALS)
if price_usdt_dai is not None:
    print(f"1 USDT = {price_usdt_dai:.6f} DAI")