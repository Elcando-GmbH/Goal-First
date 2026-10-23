# Examples

Runnable walkthroughs following *Goal First in Python*. Each script fetches
data at run time through the default provider (yfinance); nothing is stored in
this repository. Replace the `UNIVERSE` list with your own tickers.

| Script | Guide | Strategy |
|---|---|---|
| `outperformance.py` | Parts 2–4 | benchmark bias threshold, ranked by average annual return |
| `dividend.py` | Part 5, variant 1 | dividend yield threshold, ranked by average annual total return |
| `low_volatility.py` | Part 5, variant 2 | ranked by standard deviation of annual returns, lowest first |

```bash
pip install -e .
python examples/outperformance.py
```

The output is a shortlist, not a buy list. The last step is always a manual review.
