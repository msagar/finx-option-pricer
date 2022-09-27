# Finx Option Pricer
Price and visualize options with fine grained option params.

## Why?
`finx-option-pricer` was created to determine how PnL, greeks, and other metrics change for simple and complex option combos.

## Example
Here's a realistic example using options on Crude Futures

[examples/complex-option-plot.ipynb](./examples/complex-option-plot.ipynb)
```
import matplotlib.pyplot as plt
from finx_option_pricer.option import Option
from finx_option_pricer.option_plot import OptionsPlot, OptionPosition

spot_range = [65, 140]

oil_price = 102.67

# long 14d put @ 110
op1 = OptionPosition(
    quantity=1,
    option=Option(S=oil_price, K=110, T=14/252, r=0.0, sigma=0.65, option_type='p'))

# short 8d put @ 108
op2 = OptionPosition(
    quantity=-1,
    option=Option(S=oil_price, K=108, T=8/252, r=0.0, sigma=0.65, option_type='p'))

op_plot = OptionsPlot(option_positions=[op1, op2], spot_range=spot_range)

# increment 10 days, 1 day at a time
df = op_plot.gen_value_df_timeincrementing(8, 1)

# arbitrary transformations to graph the data
df.set_index("strikes", inplace=True)
columns = [f"t{i}" for i, _ in enumerate(df.columns)]
columns[-1] = "tf"
df.columns = columns

df.plot(figsize=(12, 8))
plt.hlines(0, spot_range[0], spot_range[1], color="black", linewidth=0.5)
plt.axvline(x=oil_price, color="grey", linestyle="--")
plt.axvline(x=112, color='green', linestyle="-.")
```
![Complex Option Plot](docs/complex_plot.png)

## Install

### Within a requirements.txt file
Add this line to your requirements.txt file,
```sh
git+https://github.com/westonplatter/finx-option-pricer
```

### From the command line
Clone the repo and install with pip
```sh
git clone https://github.com/westonplatter/finx-option-pricer
cd finx-option-pricer
pip install -e .
```

## Dev
```sh
git clone https://github.com/westonplatter/finx-option-pricer
cd finx-option-pricer
make env.update
# make changes
```
## Test
There are currently few to no tests.
```sh
make test
# which runs pytest .
```

## License
BSD-3. See `LICENSE` file.

NOTE - Per the BSD-3 License, you are solely responsible for decisions you make with this code.