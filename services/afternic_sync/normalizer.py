from datetime import datetime


def clean(value):
    return str(value or "").strip()


def lower(value):
    return clean(value).lower()


def money_to_float(value):
    value = clean(value)
    value = value.replace("$", "").replace(",", "")

    if not value:
        return None

    try:
        return float(value)
    except ValueError:
        return None


def parse_date(value):
    value = clean(value)

    if not value:
        return None

    formats = [
        "%Y-%m-%d",
        "%m/%d/%Y",
        "%m/%d/%y",
        "%b %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date().isoformat()
        except ValueError:
            pass

    return None


def get_field(row: dict, *possible_names):
    for name in possible_names:
        if name in row and row[name]:
            return row[name]

    lower_map = {k.lower().strip(): v for k, v in row.items()}

    for name in possible_names:
        key = name.lower().strip()
        if key in lower_map and lower_map[key]:
            return lower_map[key]

    return ""


def normalize_afternic_row(row: dict) -> dict:
    domain = lower(get_field(row, "domain", "Domain", "Domain Name", "name"))

    status = lower(get_field(row, "status", "Status", "Listing Status"))

    sale_price = money_to_float(
        get_field(row, "sale price", "Sale Price", "Sold Price", "Price")
    )

    list_price = money_to_float(
        get_field(row, "list price", "List Price", "Buy Now Price", "BIN", "Asking Price")
    )

    floor_price = money_to_float(
        get_field(row, "floor price", "Floor Price", "Minimum Offer")
    )

    sale_date = parse_date(
        get_field(row, "sale date", "Sale Date", "Sold Date", "Date Sold")
    )

    listed_date = parse_date(
        get_field(row, "listed date", "Listed Date", "Created Date")
    )

    views = get_field(row, "views", "Views", "Search Views", "Impressions")
    purchase_price = money_to_float(
        get_field(
            row,
            "purchase price",
            "Purchase Price",
            "Acquisition Cost",
            "Cost",
            "Bought For",
        )
    )
    purchase_date = parse_date(
        get_field(
            row,
            "purchase date",
            "Purchase Date",
            "Acquired Date",
            "Date Bought",
        )
    )
    registrar = get_field(row, "registrar", "Registrar", "Purchased From", "Source")

    try:
        views = int(str(views).replace(",", "")) if views else None
    except ValueError:
        views = None

    if sale_price:
        outcome = "sold"
    elif "sold" in status:
        outcome = "sold"
    elif "active" in status or "listed" in status:
        outcome = "listed"
    elif "pending" in status:
        outcome = "pending"
    else:
        outcome = status or "unknown"

    return {
        "domain": domain,
        "status": status,
        "outcome": outcome,
        "sale_price": sale_price,
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
        "registrar": registrar,
        "list_price": list_price,
        "floor_price": floor_price,
        "sale_date": sale_date,
        "listed_date": listed_date,
        "views": views,
        "raw": row,
    }


def normalize_domain_purchase_row(row: dict) -> dict:
    domain = lower(get_field(row, "domain", "Domain", "Domain Name", "name"))
    purchase_price = money_to_float(
        get_field(
            row,
            "purchase price",
            "Purchase Price",
            "Acquisition Cost",
            "Cost",
            "Bought For",
        )
    )
    purchase_date = parse_date(
        get_field(
            row,
            "purchase date",
            "Purchase Date",
            "Acquired Date",
            "Date Bought",
        )
    )
    registrar = get_field(row, "registrar", "Registrar", "Purchased From", "Source")
    notes = get_field(row, "notes", "Notes", "Reason", "Strategy")

    return {
        "domain": domain,
        "status": "purchased",
        "outcome": "purchased",
        "purchase_price": purchase_price,
        "purchase_date": purchase_date,
        "registrar": registrar,
        "notes": notes,
        "raw": row,
    }
