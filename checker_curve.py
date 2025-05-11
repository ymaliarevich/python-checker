from web3 import Web3

# --- Конфигурация ---
INFURA_URL = "https://mainnet.infura.io/v3/64867581a7784b99b648be9f819ca3d8" # Ваш RPC URL

# Curve 3pool
CURVE_3POOL_ADDRESS = "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7"
CURVE_3POOL_ABI = """
[
  {
    "name": "coins",
    "outputs": [{"type": "address", "name": ""}],
    "inputs": [{"type": "int128", "name": "arg0"}],
    "stateMutability": "view", "type": "function"
  },
  {
    "name": "get_dy",
    "outputs": [{"type": "uint256", "name": ""}],
    "inputs": [
      {"type": "int128", "name": "i"},
      {"type": "int128", "name": "j"},
      {"type": "uint256", "name": "dx"}
    ],
    "stateMutability": "view", "type": "function"
  }
]
""" # Минимальный ABI

# Адреса токенов (для сверки и удобства)
USDT_ADDRESS = "0xdAC17F958D2ee523a2206206994597C13D831ec7"
USDC_ADDRESS = "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"
DAI_ADDRESS = "0x6B175474E89094C44Da98b954EedeAC495271d0F"

# Десятичные знаки токенов (важно для корректных расчетов)
# USDT и USDC имеют 6, DAI имеет 18
TOKEN_DECIMALS = {
    USDT_ADDRESS: 6,
    USDC_ADDRESS: 6,
    DAI_ADDRESS: 18
}

# Индексы токенов в Curve 3pool (DAI:0, USDC:1, USDT:2)
# Это нужно проверить для каждого конкретного пула Curve!
CURVE_3POOL_TOKEN_INDICES = {
    DAI_ADDRESS: 0,
    USDC_ADDRESS: 1,
    USDT_ADDRESS: 2,
}


# --- Инициализация Web3 ---
w3 = Web3(Web3.HTTPProvider(INFURA_URL))

if not w3.is_connected():
    print("Ошибка: Не удалось подключиться к узлу Ethereum.")
    exit()

# --- Инициализация контракта Curve 3pool ---
curve_3pool_contract = w3.eth.contract(address=CURVE_3POOL_ADDRESS, abi=CURVE_3POOL_ABI)

def get_curve_pool_token_indices(pool_contract, known_tokens):
    """
    Пытается определить индексы известных токенов в пуле Curve.
    Примечание: Это упрощенный пример. В некоторых пулах может быть больше токенов.
    """
    indices = {}
    try:
        for i in range(len(known_tokens) + 2): # Проверим несколько первых индексов
            token_address_in_pool = pool_contract.functions.coins(i).call()
            if token_address_in_pool in known_tokens:
                indices[token_address_in_pool] = i
            if len(indices) == len(known_tokens): # Если все известные токены найдены
                break
    except Exception as e:
        # Ошибка может возникнуть, если индекс выходит за пределы количества монет в пуле
        # print(f"Примечание: достигнут конец списка монет в пуле или произошла ошибка: {e}")
        pass
    return indices

def get_curve_price(pool_contract, token_in_address, token_out_address, amount_in=1):
    """
    Получает ожидаемое количество выходного токена из пула Curve.

    :param pool_contract: Объект контракта пула Curve
    :param token_in_address: Адрес входного токена
    :param token_out_address: Адрес выходного токена
    :param amount_in: Количество входного токена (в обычных единицах, не wei)
    :return: Количество выходного токена или None в случае ошибки
    """
    token_in_address_checksum = w3.to_checksum_address(token_in_address)
    token_out_address_checksum = w3.to_checksum_address(token_out_address)

    # Получаем индексы для текущего пула
    # Для 3pool мы их уже знаем, но для других пулов это может быть динамическим
    # current_pool_indices = get_curve_pool_token_indices(pool_contract, [token_in_address_checksum, token_out_address_checksum])
    # Для 3pool используем заранее известные:
    current_pool_indices = CURVE_3POOL_TOKEN_INDICES


    if token_in_address_checksum not in current_pool_indices or token_out_address_checksum not in current_pool_indices:
        print(f"Ошибка: Один из токенов ({token_in_address_checksum} или {token_out_address_checksum}) не найден в предопределенных индексах этого пула Curve.")
        # Попытка динамического определения (может быть медленнее)
        print("Попытка динамического определения индексов...")
        dynamic_indices = get_curve_pool_token_indices(pool_contract, list(TOKEN_DECIMALS.keys()))
        print(f"Динамически определенные индексы: {dynamic_indices}")
        if token_in_address_checksum not in dynamic_indices or token_out_address_checksum not in dynamic_indices:
             print(f"Ошибка: Не удалось динамически определить индексы для токенов в пуле {pool_contract.address}.")
             return None
        idx_in = dynamic_indices[token_in_address_checksum]
        idx_out = dynamic_indices[token_out_address_checksum]
    else:
        idx_in = current_pool_indices[token_in_address_checksum]
        idx_out = current_pool_indices[token_out_address_checksum]


    decimals_in = TOKEN_DECIMALS.get(token_in_address_checksum)
    decimals_out = TOKEN_DECIMALS.get(token_out_address_checksum)

    if decimals_in is None or decimals_out is None:
        print(f"Ошибка: Не определены десятичные знаки для {token_in_address_checksum} или {token_out_address_checksum}")
        return None

    try:
        # Конвертируем количество входного токена в его наименьшие единицы
        amount_in_wei = int(amount_in * (10**decimals_in))

        # Вызов функции get_dy
        # int128 для индексов, uint256 для суммы
        amount_out_wei = pool_contract.functions.get_dy(idx_in, idx_out, amount_in_wei).call()

        # Конвертируем результат обратно из наименьших единиц
        amount_out_adjusted = amount_out_wei / (10**decimals_out)
        return amount_out_adjusted
    except Exception as e:
        print(f"Ошибка при получении цены из Curve ({pool_contract.address}) для {token_in_address} -> {token_out_address}: {e}")
        return None

# --- Проверка адресов токенов в 3pool (опционально, для уверенности) ---
print("Проверка токенов в Curve 3pool (0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7):")
try:
    print(f"Индекс 0: {curve_3pool_contract.functions.coins(0).call()}") # Ожидается DAI
    print(f"Индекс 1: {curve_3pool_contract.functions.coins(1).call()}") # Ожидается USDC
    print(f"Индекс 2: {curve_3pool_contract.functions.coins(2).call()}") # Ожидается USDT
except Exception as e:
    print(f"Не удалось получить адреса монет из пула: {e}")
print("-" * 30)

# --- Получение цен ---
print("Получение цен с Curve Finance (3pool)...\n")

# 1. USDT -> USDC через Curve 3pool
amount_usdt_in = 100 # Например, 100 USDT
price_usdt_usdc_curve = get_curve_price(curve_3pool_contract, USDT_ADDRESS, USDC_ADDRESS, amount_usdt_in)
if price_usdt_usdc_curve is not None:
    print(f"{amount_usdt_in} USDT = {price_usdt_usdc_curve:.6f} USDC (через Curve 3pool)")
    print(f"1 USDT = {(price_usdt_usdc_curve / amount_usdt_in):.6f} USDC (через Curve 3pool)\n")


# 2. USDC -> DAI через Curve 3pool
amount_usdc_in = 100 # Например, 100 USDC
price_usdc_dai_curve = get_curve_price(curve_3pool_contract, USDC_ADDRESS, DAI_ADDRESS, amount_usdc_in)
if price_usdc_dai_curve is not None:
    print(f"{amount_usdc_in} USDC = {price_usdc_dai_curve:.6f} DAI (через Curve 3pool)")
    print(f"1 USDC = {(price_usdc_dai_curve / amount_usdc_in):.6f} DAI (через Curve 3pool)\n")