"""Kalshi trading analysis script."""
import os
import json
from datetime import datetime
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
import matplotlib.pyplot as plt
import pandas as pd
from dotenv import load_dotenv
from clients import KalshiHttpClient, Environment

load_dotenv()
env = Environment.PROD
KEYID = os.getenv('DEMO_KEYID') if env == Environment.DEMO else os.getenv('PROD_KEYID')
KEYFILE = os.getenv('DEMO_KEYFILE') if env == Environment.DEMO else os.getenv('PROD_KEYFILE')

if not KEYFILE:
    raise ValueError("KEYFILE environment variable is not set.")

if not KEYID:
    raise ValueError("KEYID environment variable is not set.")

try:
    with open(KEYFILE, "rb") as key_file:
        private_key = serialization.load_pem_private_key(
            key_file.read(),
            password=None
        )
except FileNotFoundError as exc:
    raise FileNotFoundError(f"Private key file not found at {KEYFILE}") from exc
except Exception as e:
    raise ValueError(f"Error loading private key: {str(e)}") from e

if not isinstance(private_key, RSAPrivateKey):
    raise TypeError("Private key must be an RSA private key.")

client = KalshiHttpClient(
    key_id=KEYID,
    private_key=private_key,
    environment=env
)

def date_to_unix(date_string: str) -> int:
    """Convert date string to Unix timestamp."""
    dt = datetime.strptime(date_string, "%Y-%m-%d")
    return int(dt.timestamp())


dates = [
    "2024-11-05", "2024-11-04", "2024-11-03", "2024-11-02", "2024-11-01", 
    "2024-10-31", "2024-10-30", "2024-10-29", "2024-10-28", 
    "2024-10-27", "2024-10-26", "2024-10-25", "2024-10-24", 
    "2024-10-23", "2024-10-22", "2024-10-21", "2024-10-20", 
    "2024-10-19", "2024-10-18", "2024-10-17", "2024-10-16", 
    "2024-10-15", "2024-10-14", "2024-10-13", "2024-10-12", 
    "2024-10-11", "2024-10-10", "2024-10-09", "2024-10-08",
    "2024-10-07", "2024-10-06", "2024-10-05", "2024-10-04"
]

all_trump_trades = []
all_harris_trades = []

for date_str in dates:
    unix_time = date_to_unix(date_str)

    trump_trades = client.get_trades(ticker="PRES-2024-DJT", max_ts=unix_time)
    harris_trades = client.get_trades(ticker="PRES-2024-KH", max_ts=unix_time)

    all_trump_trades.extend(trump_trades['trades'])
    all_harris_trades.extend(harris_trades['trades'])

with open('all_trump_trades.json', 'w', encoding='utf-8') as f:
    json.dump(all_trump_trades, f, indent=4)
with open('all_harris_trades.json', 'w', encoding='utf-8') as f:
    json.dump(all_harris_trades, f, indent=4)


def parse_trades(trades):
    """Parse trades to extract relevant information."""
    trade_data = []
    for trade in trades:
        trade_info = {
            "created_time": trade["created_time"],
            "ticker": trade["ticker"],
            "count": trade["count"],
            "yes_price": trade["yes_price"],
            "no_price": trade["no_price"],
            "taker_side": trade["taker_side"]
        }
        trade_data.append(trade_info)
    return trade_data


def to_dataframe(trade_data: list) -> pd.DataFrame:
    """Convert trade data to a pandas DataFrame."""
    df = pd.DataFrame(trade_data)
    df['created_time'] = pd.to_datetime(df['created_time'])
    df['date'] = df['created_time'].dt.date
    return df


trump_data = parse_trades(all_trump_trades)
harris_data = parse_trades(all_harris_trades)

df_trump = to_dataframe(trump_data)
df_harris = to_dataframe(harris_data)

# --- analysis starts here ---

OUTPUT_DIRECTORY = "plots/"
os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)

# example 1: trade volume over time for trump
df_trump_yes = df_trump[df_trump['taker_side'] == 'yes']
df_trump_no = df_trump[df_trump['taker_side'] == 'no']

trade_volume_by_day_trump_yes = df_trump_yes.groupby('date')['count'].sum()
trade_volume_by_day_trump_no = df_trump_no.groupby('date')['count'].sum()

# original
plt.figure(figsize=(10, 6))
plt.plot(trade_volume_by_day_trump_yes.index, trade_volume_by_day_trump_yes,
         marker='o', label="Yes Trades", color='green')
plt.plot(trade_volume_by_day_trump_no.index, trade_volume_by_day_trump_no,
         marker='o', label="No Trades", color='red')
plt.title("Trade Volume Over Time (PRES-2024-DJT)")
plt.xlabel("Date")
plt.ylabel("Total Trade Volume")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'trade_volume_trump_yes_no.png'))
plt.close()

# --- industry notation for object oriented plotting ---
# fig, ax = plt.subplots(figsize=(10, 6))

# ax.plot(trade_volume_by_day_trump_yes.index, trade_volume_by_day_trump_yes,
# marker='o', label="Yes Trades", color='green')
# ax.plot(trade_volume_by_day_trump_no.index, trade_volume_by_day_trump_no,
# marker='o', label="No Trades", color='red')

# ax.set_title("Trade Volume Over Time (PRES-2024-DJT)")
# ax.set_xlabel("Date")
# ax.set_ylabel("Total Trade Volume")
# ax.grid(True)
# ax.legend()
# plt.xticks(rotation=45)

# fig.tight_layout()
# fig.savefig(os.path.join(OUTPUT_DIRECTORY,
# 'trade_volume_trump_yes_no_object_oriented_plotting.png'))
# plt.close(fig)


# --- Seaborn plot, needs dataframe format ---
# df_trump_volume = pd.DataFrame({
#     'date': trade_volume_by_day_trump_yes.index.tolist()
# + trade_volume_by_day_trump_no.index.tolist(),
#     'volume': trade_volume_by_day_trump_yes.tolist()
# + trade_volume_by_day_trump_no.tolist(),
#     'taker_side': ['yes'] * len(trade_volume_by_day_trump_yes) + ['no'] *
# len(trade_volume_by_day_trump_no)
# })

# import seaborn as sns
# sns.set_theme(style="whitegrid")

# fig, ax = plt.subplots(figsize=(10, 6))
# sns.lineplot(data=df_trump_volume, x='date', y='volume', hue='taker_side',
# marker='o', ax=ax)

# ax.set_title("Trade Volume Over Time (PRES-2024-DJT)")
# ax.set_xlabel("Date")
# ax.set_ylabel("Total Trade Volume")
# plt.xticks(rotation=45)
# fig.tight_layout()

# fig.savefig(os.path.join(OUTPUT_DIRECTORY, 'trade_volume_trump_yes_no_seaborn.png'))
# plt.close(fig)

# likewise for harris
df_harris_yes = df_harris[df_harris['taker_side'] == 'yes']
df_harris_no = df_harris[df_harris['taker_side'] == 'no']

trade_volume_by_day_harris_yes = df_harris_yes.groupby('date')['count'].sum()
trade_volume_by_day_harris_no = df_harris_no.groupby('date')['count'].sum()

plt.figure(figsize=(10, 6))
plt.plot(trade_volume_by_day_harris_yes.index, trade_volume_by_day_harris_yes,
         marker='o', label="Yes Trades", color='blue')
plt.plot(trade_volume_by_day_harris_no.index, trade_volume_by_day_harris_no,
         marker='o', label="No Trades", color='orange')
plt.title("Trade Volume Over Time (PRES-2024-KH)")
plt.xlabel("Date")
plt.ylabel("Total Trade Volume")
plt.grid(True)
plt.xticks(rotation=45)
plt.legend()
plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'trade_volume_harris_yes_no.png'))
plt.close()


# example 2: price analysis (yes/no) for trump
plt.figure(figsize=(10, 6))
plt.plot(df_trump['created_time'], df_trump['yes_price'], label="Yes Price (Trump)", color='red')
plt.plot(df_trump['created_time'], df_trump['no_price'], label="No Price (Trump)", color='blue')
plt.title("Price Trends for Trump (PRES-2024-DJT)")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'price_trends_trump.png'))
plt.close()


# likewise for harris
plt.figure(figsize=(10, 6))
plt.plot(df_harris['created_time'], df_harris['yes_price'], label="Yes Price (Harris)",color='blue')
plt.plot(df_harris['created_time'], df_harris['no_price'], label="No Price (Harris)", color='red')
plt.title("Price Trends for Harris (PRES-2024-KH)")
plt.xlabel("Time")
plt.ylabel("Price")
plt.legend()
plt.xticks(rotation=45)
plt.grid(True)
plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'price_trends_harris.png'))
plt.close()


# example 4: tetail vs institutional trades
THRESHOLD = 10000  # higher than this is institutional, lower is retail

df_trump['investor_type'] = df_trump['count'].apply(lambda x:
    'Retail' if x < THRESHOLD else 'Institutional')
df_harris['investor_type'] = df_harris['count'].apply(lambda x:
    'Retail' if x < THRESHOLD else 'Institutional')

retail_trump = df_trump[df_trump['investor_type'] ==
                        'Retail'].groupby('date')['count'].sum()
institutional_trump = df_trump[df_trump['investor_type'] ==
                               'Institutional'].groupby('date')['count'].sum()

retail_harris = df_harris[df_harris['investor_type'] ==
                          'Retail'].groupby('date')['count'].sum()
institutional_harris = df_harris[df_harris['investor_type'] ==
                                 'Institutional'].groupby('date')['count'].sum()

plt.figure(figsize=(12, 8))

# trump
plt.subplot(2, 1, 1)
plt.plot(retail_trump.index, retail_trump, label='Retail', color='blue', marker='o')
plt.plot(institutional_trump.index, institutional_trump,
         label='Institutional', color='red', marker='x')
plt.title('Trade Volume for Trump (PRES-2024-DJT)')
plt.xlabel('Date')
plt.ylabel('Total Trade Volume')
plt.legend()
plt.grid(True)

# harris
plt.subplot(2, 1, 2)
plt.plot(retail_harris.index, retail_harris, label='Retail', color='blue', marker='o')
plt.plot(institutional_harris.index, institutional_harris,
         label='Institutional', color='red', marker='x')
plt.title('Trade Volume for Harris (PRES-2024-KH)')
plt.xlabel('Date')
plt.ylabel('Total Trade Volume')
plt.legend()
plt.grid(True)

plt.xticks(rotation=45)

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIRECTORY, 'retail_vs_institutional_trade_volume.png'))
plt.close()
