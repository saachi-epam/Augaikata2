import csv

portfolios = {
    "P1": {
        "cash_balance": 10000,
        "restricted_securities": ["XYZ"],
        "max_position_pct": 0.25,
        "current_holdings": [("AAPL", 50, 150.0), ("BND1", 100, 98.0)],
    }
}

def get_held_quantity(portfolio, security_id):
    held = 0
    for sec_id, qty, market_price in portfolio["current_holdings"]:
        if sec_id == security_id:
            held += qty
    return held

def check_trade(trade, portfolio):
    # Step 1: validate (csv values are strings, so convert them first)
    try:
        quantity = float(trade["quantity"])
        price = float(trade["price"])
    except (ValueError, TypeError, KeyError):
        return "Rejected", "Invalid trade data."

    if not (quantity > 0 and price > 0):
        return "Rejected", "Invalid trade data."
    if trade["action"] not in ["Buy", "Sell"]:
        return "Rejected", "Invalid trade data."

    # Step 2: restricted security
    if trade["security_id"] in portfolio["restricted_securities"]:
        return "Rejected", "Security is restricted for this portfolio."

    held = get_held_quantity(portfolio, trade["security_id"])
    cost = quantity * price

    # Step 3: sell check
    if trade["action"] == "Sell" and held < quantity:
        return "Rejected", "Insufficient holdings to sell."

    # Step 4: buy affordability
    if trade["action"] == "Buy" and cost > portfolio["cash_balance"]:
        return "Rejected", "Insufficient cash for this buy order."

    # Step 5: concentration check (Buy only)
    if trade["action"] == "Buy":
        post_trade_cash = portfolio["cash_balance"] - cost
        post_trade_quantity = held + quantity
        post_trade_value = post_trade_quantity * price

        value_of_other_holdings = 0
        for sec_id, qty, market_price in portfolio["current_holdings"]:
            if sec_id != trade["security_id"]:
                value_of_other_holdings += qty * market_price

        total_value_after = post_trade_cash + post_trade_value + value_of_other_holdings
        position_pct = post_trade_value / total_value_after

        if position_pct > portfolio["max_position_pct"]:
            return "Needs Manual Sign-off", "Exceeds maximum position concentration — requires approval."

    # Step 6: approved
    return "Approved", "Passed all checks."


# Read trades as a list of dictionaries
with open("trades_test.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    fieldnames = reader.fieldnames
    trades = list(reader)

# Process each trade
for trade in trades:
    portfolio = portfolios.get(trade.get("portfolio_id"))
    if portfolio is None:
        decision, reason = "Rejected", "Unknown portfolio."
    else:
        decision, reason = check_trade(trade, portfolio)
    trade["decision"] = decision
    trade["reason"] = reason

# Print results
for trade in trades:
    print(trade)

# Write results to a new CSV file
output_fields = list(fieldnames) + ["decision", "reason"]
with open("results.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=output_fields)
    writer.writeheader()
    writer.writerows(trades)