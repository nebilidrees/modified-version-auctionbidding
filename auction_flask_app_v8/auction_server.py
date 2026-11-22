from flask import Flask, render_template, request, redirect, url_for
import json
import random
from datetime import datetime
from pathlib import Path
from auction_models import (
    Auction, Seller, ItemSpecification, Bidder, Bid, Payment,
)

auction_manager = Flask(__name__)

STANDARD_CATEGORIES = [
    "Automobiles & Commercial Vehicles",
    "Smartphones & Mobile Devices",
    "Computers & Enterprise Electronics",
    "Real Estate & Landed Property",
    "Industrial Machinery & Equipment",
    "Fine Art, Jewelry & Collectibles",
]

PARTICIPATION_FEE = 30000
DATA_FILE = Path(__file__).resolve().with_name("auctions.json")
LEGACY_ITEMS_FILE = Path(__file__).resolve().with_name("bids_items.json")


def import_legacy_items(data):
    if not LEGACY_ITEMS_FILE.exists():
        return False

    with LEGACY_ITEMS_FILE.open("r", encoding="utf-8") as source_file:
        legacy_items = json.load(source_file)

    existing_ids = {item.get("item_id") for item in data["items"]}
    auctions_by_event = {
        (auction.get("auction_name", "").casefold(), auction.get("location", "").casefold()): auction
        for auction in data["auctions"]
        if auction.get("status", "Open") != "Closed"
    }
    changed = False

    for item_id, details in legacy_items.items():
        if item_id in existing_ids:
            continue

        starting_price = int(float(details.get("base price", 0)))
        event_key = (
            details.get("event_name", "").casefold(),
            details.get("event_location", "").casefold(),
        )
        matching_auction = auctions_by_event.get(event_key)
        legacy_status = details.get("status", "AVAILABLE").upper()
        item_status = "Available" if legacy_status == "AVAILABLE" else "Sold" if legacy_status in {"CLAIMED", "SOLD"} else legacy_status.title()

        data["items"].append({
            "item_id": item_id,
            "item_name": details.get("name", item_id).title(),
            "category": details.get("category", "General"),
            "condition": details.get("condition", "New"),
            "starting_price": starting_price,
            "reserved_price": starting_price + 50000,
            "description": "",
            "status": item_status,
            "seller_id": details.get("seller_id", ""),
            "seller_name": details.get("seller_name", ""),
            "auction_id": matching_auction["auction_id"] if matching_auction else "",
        })
        existing_ids.add(item_id)
        changed = True

    return changed


def load_data():
    try:
        with DATA_FILE.open("r", encoding="utf-8") as doc:
            data = json.load(doc)
    except FileNotFoundError:
        data = {}
    data.setdefault("auctions", [])
    data.setdefault("sellers", [])
    data.setdefault("items", [])
    data.setdefault("bidders", [])
    data.setdefault("bids", [])
    data.setdefault("winners", [])
    data.setdefault("payments", [])
    data.setdefault("auction_results", [])
    if import_legacy_items(data):
        save_data(data)
    return data


def save_data(data):
    with DATA_FILE.open("w", encoding="utf-8") as doc:
        json.dump(data, doc, indent=4)


def make_auction(auction_data):
    return Auction(
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )


def make_seller(seller_data, auction_data):
    return Seller(
        seller_data.get("seller_id", ""),
        seller_data.get("name", ""),
        seller_data.get("company", ""),
        seller_data.get("contact", ""),
        seller_data.get("email_address", ""),
        seller_data.get("seller_status", "Registered"),
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )


def make_bidder(bidder_data, auction_data):
    return Bidder(
        bidder_data.get("name", ""),
        bidder_data.get("contact", ""),
        bidder_data.get("address", ""),
        bidder_data.get("bidders_id", ""),
        bidder_data.get("gender", ""),
        bidder_data.get("birth_year", ""),
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )


def make_item(item_data, seller_data, auction_data):
    specification = ItemSpecification(
        item_data.get("item_id", ""),
        item_data.get("item_name", ""),
        item_data.get("category", "General"),
        item_data.get("condition", "New"),
        int(item_data.get("starting_price", 0)),
        int(item_data.get("reserved_price", 0)),
        item_data.get("status", "Available"),
        seller_data.get("seller_id", ""),
        seller_data.get("name", ""),
        seller_data.get("company", ""),
        seller_data.get("contact", ""),
        seller_data.get("email_address", ""),
        seller_data.get("seller_status", "Registered"),
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )
    specification.item_name = item_data.get("item_name", "")
    specification.starting_price = int(item_data.get("starting_price", 0))
    specification.seller = make_seller(seller_data, auction_data)
    specification.auction = make_auction(auction_data)
    return specification


def make_bid(bid_data, bidder_data, item_data, seller_data, auction_data):
    return Bid(
        bid_data["amount"],
        bid_data.get("date", ""),
        bid_data.get("time", ""),
        bidder_data.get("name", ""),
        bidder_data.get("contact", ""),
        bidder_data.get("address", ""),
        bidder_data.get("bidders_id", ""),
        bidder_data.get("gender", ""),
        bidder_data.get("birth_year", ""),
        item_data["item_id"],
        item_data["item_name"],
        item_data.get("category", "General"),
        item_data.get("condition", "New"),
        int(item_data.get("starting_price", 0)),
        int(item_data.get("reserved_price", 0)),
        item_data.get("status", "Available"),
        seller_data.get("seller_id", ""),
        seller_data.get("name", ""),
        seller_data.get("company", ""),
        seller_data.get("contact", ""),
        seller_data.get("email_address", ""),
        seller_data.get("seller_status", "Registered"),
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )


def make_payment(payment_id, bid_id, transaction_id, currency, payment_method,
                 bid_data, bidder_data, item_data, seller_data, auction_data):
    return Payment(
        payment_id,
        bid_id,
        transaction_id,
        currency,
        payment_method,
        bid_data["amount"],
        bid_data.get("date", ""),
        bid_data.get("time", ""),
        bidder_data.get("name", ""),
        bidder_data.get("contact", ""),
        bidder_data.get("address", ""),
        bidder_data.get("bidders_id", ""),
        bidder_data.get("gender", ""),
        bidder_data.get("birth_year", ""),
        item_data["item_id"],
        item_data["item_name"],
        item_data.get("category", "General"),
        item_data.get("condition", "New"),
        int(item_data.get("starting_price", 0)),
        int(item_data.get("reserved_price", 0)),
        item_data.get("status", "Available"),
        seller_data.get("seller_id", ""),
        seller_data.get("name", ""),
        seller_data.get("company", ""),
        seller_data.get("contact", ""),
        seller_data.get("email_address", ""),
        seller_data.get("seller_status", "Registered"),
        auction_data["auction_id"],
        auction_data["date"],
        auction_data["start_time"],
        auction_data["end_time"],
        auction_data["location"],
        auction_data["auction_name"],
    )


def next_auto_id(prefix, existing_ids, digits=3):
    highest = 0
    for item_id in existing_ids:
        if item_id and item_id.startswith(prefix) and item_id[len(prefix):].isdigit():
            num = int(item_id[len(prefix):])
            if num > highest:
                highest = num
    return f"{prefix}{highest + 1:0{digits}d}"


def active_bids(data):
    """Return bids that have not been withdrawn by their bidder."""
    return [bid for bid in data["bids"] if bid.get("bid_status", "Active") == "Active"]


def current_highest_bid_per_item(data):
    highest_by_item = {}
    for bid in active_bids(data):
        current = highest_by_item.get(bid["item_id"])
        if current is None or bid["amount"] > current["amount"]:
            highest_by_item[bid["item_id"]] = bid
    return list(highest_by_item.values())


def latest_active_bid_ids(data):
    latest = set()
    seen_bidder_items = set()
    for bid in reversed(data["bids"]):
        if bid.get("bid_status", "Active") != "Active":
            continue
        bidder_item = (bid.get("bidders_id"), bid.get("item_id"))
        if bidder_item not in seen_bidder_items:
            seen_bidder_items.add(bidder_item)
            if bid.get("bid_id"):
                latest.add(bid["bid_id"])
    return latest


def auction_is_open(data, auction_id):
    auction = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    # Existing saved auctions pre-date the status field and remain usable.
    return auction is not None and auction.get("status", "Open") == "Open"


def rebuild_bid_objects(data):
    bid_objects = []
    for b in active_bids(data):
        auction_data = next(
            (a for a in data["auctions"] if a["auction_id"] == b.get("auction_id")),
            {},
        )
        seller_data = next(
            (s for s in data["sellers"] if s["seller_id"] == b.get("seller_id")),
            {},
        )
        bidder_data = next(
            (bidder for bidder in data["bidders"] if bidder["bidders_id"] == b.get("bidders_id")),
            {
                "name": b.get("bidder_name", ""),
                "contact": b.get("contact", ""),
                "address": b.get("address", ""),
                "bidders_id": b.get("bidders_id", ""),
                "gender": b.get("gender", ""),
                "birth_year": b.get("birth_year", ""),
            },
        )
        item_data = next(
            (item for item in data["items"] if item["item_id"] == b.get("item_id")),
            b,
        )
        bid_objects.append(
            make_bid(b, bidder_data, item_data, seller_data, auction_data)
            if auction_data
            else None
        )
    bid_objects = [bid for bid in bid_objects if bid is not None]

    return bid_objects


def build_summary_context(data):
    bid_objects = rebuild_bid_objects(data)
    highest_bid = Auction.find_highest_bid(None, bid_objects)
    return {
        "auction_count": len(data["auctions"]),
        "seller_count": len(data["sellers"]),
        "item_count": len(data["items"]),
        "bidder_count": len(data["bidders"]),
        "bid_count": len(active_bids(data)),
        "winner_count": len(data["winners"]),
        "payment_count": len(data["payments"]),
        "total_bid_amount": sum(b["amount"] for b in active_bids(data)),
        "highest_bid": highest_bid.amount if highest_bid else 0,
        "highest_bidder": highest_bid.bidder_name if highest_bid else "None",
    }


# --- HOME (LANDING PAGE) & SYSTEM OVERVIEW ROUTES ---
@auction_manager.route("/")
def index_page():
    data = load_data()
    context = build_summary_context(data)
    return render_template("index.html", context=context)


# --- AUCTIONS ROUTES ---
@auction_manager.route("/auctions")
def auctions_page():
    data = load_data()
    return render_template(
        "auctions.html",
        auctions=data["auctions"],
        status_message=request.args.get("message", ""),
    )


@auction_manager.route("/add_auction", methods=["POST"])
def add_auction():
    data = load_data()
    auto_auction_id = next_auto_id("AUC", [a["auction_id"] for a in data["auctions"]], digits=3)

    auction = Auction(
        auction_id=auto_auction_id,
        date=request.form["date"].strip(),
        start_time=request.form["start_time"].strip(),
        end_time=request.form["end_time"].strip(),
        location=request.form["location"].strip(),
        auction_name=request.form["auction_name"].strip(),
    )
    data["auctions"].append({
        "auction_id": auction.auction_id,
        "date": auction.date,
        "start_time": auction.start_time,
        "end_time": auction.end_time,
        "location": auction.location,
        "auction_name": auction.auction_name,
        "status": "Scheduled",
    })
    save_data(data)
    return redirect(url_for("auctions_page"))


@auction_manager.route("/start_auction/<auction_id>", methods=["POST"])
def start_auction(auction_id):
    data = load_data()
    auction = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    if auction is None:
        return redirect(url_for("auctions_page", message="Auction not found."))
    if auction.get("status", "Open") == "Closed":
        return redirect(url_for("auctions_page", message="A closed auction cannot be started again."))

    auction_object = Auction(
        auction["auction_id"],
        auction["date"],
        auction["start_time"],
        auction["end_time"],
        auction["location"],
        auction["auction_name"],
    )
    auction_object.start_auction()
    auction["status"] = "Open"
    save_data(data)
    return redirect(url_for("auctions_page", message="Auction started. Bidding is now open."))


@auction_manager.route("/close_auction/<auction_id>", methods=["POST"])
def close_auction(auction_id):
    data = load_data()
    auction = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    if auction is None:
        return redirect(url_for("winners_page", message="Auction not found."))
    if auction.get("status", "Open") != "Open":
        return redirect(url_for("winners_page", message="Only an open auction can be closed."))

    auction_items = [item for item in data["items"] if item.get("auction_id") == auction_id]
    auction_bids = [
        bid for bid in active_bids(data)
        if bid.get("auction_id") == auction_id
    ]
    result = {
        "auction_id": auction_id,
        "auction_name": auction["auction_name"],
        "date": auction["date"],
        "location": auction["location"],
        "items": [],
    }
    for item in auction_items:
        item_bids = [bid for bid in auction_bids if bid.get("item_id") == item["item_id"]]
        winning_bid = max(item_bids, key=lambda bid: bid["amount"], default=None)
        item_result = {
            "item_id": item["item_id"],
            "item_name": item["item_name"],
            "starting_price": item["starting_price"],
            "valid_bid_count": len(item_bids),
        }

        if winning_bid is None:
            item_result.update({
                "sale_status": "Unsold",
                "payment_status": "Not applicable",
            })
        else:
            bidder = next(
                (b for b in data["bidders"] if b.get("bidders_id") == winning_bid.get("bidders_id")),
                None,
            )
            fee_paid = int(bidder.get("participation_fee_paid", 0) or 0) if bidder else 0
            eligible_winner = fee_paid >= PARTICIPATION_FEE
            if fee_paid < PARTICIPATION_FEE:
                item_result.update({
                    "sale_status": "Payment not allowed",
                    "payment_status": "Not applicable",
                })
            else:
                winner_id = next_auto_id(
                    "WIN", [winner["winner_id"] for winner in data["winners"]], digits=3
                )
                winner = {
                    "winner_id": winner_id,
                    "auction_id": auction_id,
                    "auction_name": auction["auction_name"],
                    "bidders_id": winning_bid["bidders_id"],
                    "name": winning_bid["bidder_name"],
                    "contact": winning_bid.get("contact", ""),
                    "item_id": item["item_id"],
                    "item_name": item["item_name"],
                    "final_bid": winning_bid["amount"],
                    "added_fee": 0,
                    "total_amount_payable": winning_bid["amount"],
                    "eligible_for_item_payment": True,
                    "payment_status": "Pending",
                }
                data["winners"].append(winner)
                item["status"] = "Sold"
                item_result.update({
                    "sale_status": "Sold",
                    "winner_id": winning_bid["bidders_id"],
                    "winner_name": winning_bid["bidder_name"],
                    "final_bid": winning_bid["amount"],
                    "payment_status": "Pending",
                })
            for bid in auction_bids:
                if bid.get("item_id") == item["item_id"]:
                    bid["bid_status"] = (
                        "Winning bid" if bid is winning_bid and eligible_winner else "Outbid"
                    )
                    bid["payment_status"] = (
                        "Pending" if bid is winning_bid and eligible_winner else "Not applicable"
                    )

        result["items"].append(item_result)

    data["auction_results"].append(result)
    auction["status"] = "Closed"
    save_data(data)
    return redirect(url_for("winners_page", message="Auction closed. Results and pending payments are below."))


# --- SELLERS & MULTI-ITEM REGISTRATION ROUTES ---
@auction_manager.route("/sellers")
def sellers_page():
    data = load_data()
    selectable_auctions = [
        auction for auction in data["auctions"]
        if auction.get("status", "Open") != "Closed"
    ]
    try:
        item_slots = int(request.args.get("item_slots", 1))
    except ValueError:
        item_slots = 1
    item_slots = max(1, min(item_slots, 10))

    return render_template(
        "sellers.html",
        sellers=[
            dict(seller, listed_items=[
                item["item_name"] for item in data["items"]
                if item.get("seller_id") == seller["seller_id"]
            ])
            for seller in data["sellers"]
        ],
        auctions=selectable_auctions,
        items=data["items"],
        categories=STANDARD_CATEGORIES,
        item_slots=item_slots,
        status_message=request.args.get("message", ""),
    )


@auction_manager.route("/add_seller", methods=["POST"])
def add_seller():
    data = load_data()
    auction_id = request.form["auction_id"].strip()
    matched_auc_dict = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    if not matched_auc_dict or matched_auc_dict.get("status", "Open") == "Closed":
        return redirect(url_for("sellers_page", message="Choose an auction that has not been closed."))

    email_address = request.form["email_address"].strip()
    if any(s["email_address"].casefold() == email_address.casefold() for s in data["sellers"]):
        return redirect(url_for("sellers_page", message="A seller with that email address is already registered."))

    existing_sellers = [
        make_seller(s, matched_auc_dict)
        for s in data["sellers"]
    ]
    matched_auc = make_auction(matched_auc_dict)
    seller = make_seller({
        "seller_id": "",
        "name": request.form["name"].strip(),
        "company": request.form["company"].strip(),
        "contact": request.form["contact"].strip(),
        "email_address": email_address,
        "seller_status": "Not Registered",
    }, matched_auc_dict)
    seller.generate_seller_id(existing_sellers)
    seller.seller_status = "Registered"

    data["sellers"].append({
        "seller_id": seller.seller_id,
        "name": seller.name,
        "company": seller.company,
        "contact": seller.contact,
        "email_address": seller.email_address,
        "seller_status": seller.seller_status,
        "auction_id": auction_id,
    })

    item_names = request.form.getlist("item_name[]")
    categories = request.form.getlist("category[]")
    conditions = request.form.getlist("condition[]")
    starting_prices = request.form.getlist("starting_price[]")
    reserved_prices = request.form.getlist("reserved_price[]")
    descriptions = request.form.getlist("description[]")

    for idx, raw_name in enumerate(item_names):
        clean_name = raw_name.strip()
        if not clean_name:
            continue

        auto_item_id = next_auto_id(
            "ITM",
            [i["item_id"] for i in data["items"]] + [b["item_id"] for b in data["bids"]],
            digits=3,
        )
        category = categories[idx].strip() if idx < len(categories) else STANDARD_CATEGORIES[0]
        condition = conditions[idx].strip() if idx < len(conditions) else "New"
        if condition not in {"New", "Used"}:
            return redirect(url_for("sellers_page", message="Item condition must be New or Used."))
        try:
            starting_price = int(starting_prices[idx]) if idx < len(starting_prices) else 0
            reserved_price = int(reserved_prices[idx]) if idx < len(reserved_prices) else 0
        except ValueError:
            return redirect(url_for("sellers_page", message="Item prices must be whole numbers."))
        if starting_price <= 0 or reserved_price < starting_price:
            return redirect(url_for("sellers_page", message="Each reserve price must be at least its positive starting price."))
        description = descriptions[idx].strip() if idx < len(descriptions) else ""

        item_obj = make_item({
            "item_id": auto_item_id,
            "item_name": clean_name,
            "category": category,
            "condition": condition,
            "starting_price": starting_price,
            "reserved_price": reserved_price,
            "status": "Available",
        }, {
            "seller_id": seller.seller_id,
            "name": seller.name,
            "company": seller.company,
            "contact": seller.contact,
            "email_address": seller.email_address,
            "seller_status": seller.seller_status,
        }, matched_auc_dict)
        seller.set_starting_price(item_obj, starting_price)
        seller.reserve_price(item_obj, reserved_price)
        if description:
            seller.set_description_of_item(item_obj, description)

        data["items"].append({
            "item_id": item_obj.item_id,
            "item_name": item_obj.item_name,
            "category": item_obj.category,
            "condition": item_obj.condition,
            "starting_price": starting_price,
            "reserved_price": reserved_price,
            "description": description,
            "status": item_obj.status,
            "seller_id": seller.seller_id,
            "seller_name": seller.name,
            "auction_id": auction_id,
        })

    save_data(data)
    return redirect(url_for("sellers_page"))


@auction_manager.route("/add_seller_item", methods=["POST"])
def add_seller_item():
    data = load_data()
    seller_id = request.form["seller_id"].strip()
    auction_id = request.form["auction_id"].strip()

    matched_sel_dict = next((s for s in data["sellers"] if s["seller_id"] == seller_id), None)
    matched_auc_dict = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    if not matched_sel_dict or not matched_auc_dict or matched_auc_dict.get("status", "Open") == "Closed":
        return redirect(url_for("items_page", message="Choose a registered seller and an auction that has not been closed."))
    if matched_sel_dict.get("auction_id") != auction_id:
        return redirect(url_for("items_page", message="Choose the auction assigned to this seller."))

    matched_auc = make_auction(matched_auc_dict)
    matched_sel = make_seller(matched_sel_dict, matched_auc_dict)

    auto_item_id = next_auto_id(
        "ITM",
        [i["item_id"] for i in data["items"]] + [b["item_id"] for b in data["bids"]],
        digits=3,
    )
    item_name = request.form["item_name"].strip()
    category = request.form["category"].strip()
    condition = request.form["condition"].strip()
    if condition not in {"New", "Used"}:
        return redirect(url_for("items_page", message="Item condition must be New or Used."))
    try:
        starting_price = int(request.form["starting_price"])
        reserved_price = int(request.form["reserved_price"])
    except ValueError:
        return redirect(url_for("items_page", message="Item prices must be whole numbers."))
    if starting_price <= 0 or reserved_price < starting_price:
        return redirect(url_for("items_page", message="The reserve price must be at least the positive starting price."))
    description = request.form.get("description", "").strip()

    item_obj = make_item({
        "item_id": auto_item_id,
        "item_name": item_name,
        "category": category,
        "condition": condition,
        "starting_price": starting_price,
        "reserved_price": reserved_price,
        "status": "Available",
    }, matched_sel_dict, matched_auc_dict)
    if matched_sel:
        matched_sel.set_starting_price(item_obj, starting_price)
        matched_sel.reserve_price(item_obj, reserved_price)
        if description:
            matched_sel.set_description_of_item(item_obj, description)

    data["items"].append({
        "item_id": item_obj.item_id,
        "item_name": item_obj.item_name,
        "category": item_obj.category,
        "condition": item_obj.condition,
        "starting_price": starting_price,
        "reserved_price": reserved_price,
        "description": description,
        "status": item_obj.status,
        "seller_id": seller_id,
        "seller_name": matched_sel_dict["name"] if matched_sel_dict else "",
        "auction_id": auction_id,
    })
    save_data(data)
    return redirect(url_for("items_page"))


@auction_manager.route("/toggle_seller_status/<seller_id>", methods=["POST"])
def toggle_seller_status(seller_id):
    data = load_data()
    for s in data["sellers"]:
        if s["seller_id"] == seller_id:
            s["seller_status"] = "Registered" if s["seller_status"] == "Not Registered" else "Not Registered"
            break
    save_data(data)
    return redirect(url_for("sellers_page"))


# --- BIDDERS REGISTRATION & AVAILABLE-ITEMS BIDDING ROUTES ---
@auction_manager.route("/bidders")
def bidders_page():
    data = load_data()
    selectable_auctions = [
        auction for auction in data["auctions"]
        if auction.get("status", "Open") != "Closed"
    ]
    available_items = [
        i for i in data["items"]
        if i.get("status", "Available") == "Available" and auction_is_open(data, i.get("auction_id"))
    ]
    error_msg = request.args.get("error", "")

    highest_by_item = {}
    for b in active_bids(data):
        iid = b.get("item_id")
        if iid and b["amount"] > highest_by_item.get(iid, 0):
            highest_by_item[iid] = b["amount"]
    selected_bidder_id = request.args.get("bidder_id", "").strip()
    selected_bidder = next(
        (b for b in data["bidders"] if b.get("bidders_id") == selected_bidder_id),
        None,
    )
    bidder_history = [
        bid for bid in data["bids"]
        if selected_bidder and bid.get("bidders_id") == selected_bidder_id
    ]

    return render_template(
        "bidders.html",
        bidders=data["bidders"],
        bids=data["bids"],
        auctions=selectable_auctions,
        available_items=available_items,
        highest_by_item=highest_by_item,
        error_msg=error_msg,
        selected_bidder=selected_bidder,
        bidder_history=bidder_history,
    )


@auction_manager.route("/add_bidder", methods=["POST"])
def add_bidder():
    data = load_data()

    # Enforce mandatory participation registration fee checkbox (UGX 30,000)
    fee_confirmed = request.form.get("participation_fee_paid") == "yes"
    if not fee_confirmed:
        return redirect(
            url_for(
                "bidders_page",
                error="Registration blocked: Bidder must pay and confirm the UGX 30,000 participation fee to register for the bidding session.",
            )
        )

    existing_bidders = [
        make_bidder(reg, next((a for a in data["auctions"] if a["auction_id"] == reg.get("auction_id")), {
            "auction_id": reg.get("auction_id", ""),
            "date": "",
            "start_time": "",
            "end_time": "",
            "location": "",
            "auction_name": "",
        }))
        for reg in data["bidders"]
    ] + [
        make_bidder({
            "name": b["bidder_name"],
            "bidders_id": b.get("bidders_id", ""),
            "contact": b.get("contact", ""),
            "address": b.get("address", ""),
            "gender": b.get("gender", ""),
            "birth_year": b.get("birth_year", ""),
        }, next((a for a in data["auctions"] if a["auction_id"] == b.get("auction_id")), {
            "auction_id": b.get("auction_id", ""),
            "date": "",
            "start_time": "",
            "end_time": "",
            "location": "",
            "auction_name": "",
        }))
        for b in data["bids"]
    ]

    auction_id = request.form.get("auction_id", "").strip()
    matched_auc_dict = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    if not matched_auc_dict or matched_auc_dict.get("status", "Open") == "Closed":
        return redirect(url_for("bidders_page", error="Choose an auction that has not been closed."))
    matched_auc = make_auction(matched_auc_dict)

    birth_date = request.form.get("birth_date", "").strip()
    try:
        datetime.strptime(birth_date, "%d-%m-%Y")
    except ValueError:
        return redirect(url_for("bidders_page", error="Enter a valid birth date in DD-MM-YYYY format."))

    bidder = make_bidder({
        "name": request.form["name"].strip(),
        "contact": request.form["contact"].strip(),
        "address": request.form["address"].strip(),
        "bidders_id": "",
        "gender": request.form.get("gender", "").strip(),
        "birth_year": birth_date,
    }, matched_auc_dict)
    bidder.generate_bidder_id(existing_bidders)
    bidder.make_payment(PARTICIPATION_FEE)
    bidder.register()

    data["bidders"].append({
        "bidders_id": bidder.bidders_id,
        "name": bidder.name,
        "contact": bidder.contact,
        "address": bidder.address,
        "gender": bidder.gender,
        "birth_year": bidder.birth_year,
        "auction_id": auction_id,
        "participation_fee_paid": PARTICIPATION_FEE,
        "status": "Registered (Fee Paid)",
    })
    save_data(data)
    return redirect(url_for("bidders_page"))


# --- BIDS, COMPOSED AUCTION ITEMS & COMPOSED BIDDERS ROUTES ---
@auction_manager.route("/bids")
def bids_page():
    data = load_data()
    bid_objects = rebuild_bid_objects(data)
    highest_bid = Auction.find_highest_bid(None, bid_objects)
    available_items = [
        i for i in data["items"]
        if i.get("status", "Available") == "Available" and auction_is_open(data, i.get("auction_id"))
    ]

    context = {
        "count": len(active_bids(data)),
        "total_amount": sum(b["amount"] for b in active_bids(data)),
        "highest_bid": highest_bid.amount if highest_bid else 0,
        "highest_bidder": highest_bid.bidder_name if highest_bid else "None",
        "bid_list": data["bids"],
        "auctions": data["auctions"],
        "sellers": data["sellers"],
        "items": available_items,
        "bidders": data["bidders"],
        "categories": STANDARD_CATEGORIES,
        "current_leaders": current_highest_bid_per_item(data),
        "latest_active_bid_ids": latest_active_bid_ids(data),
    }
    return render_template(
        "bids.html",
        context=context,
        status_message=request.args.get("message", ""),
    )


@auction_manager.route("/add_bid", methods=["POST"])
def add_bid():
    data = load_data()
    redirect_target = request.form.get("redirect_to", "bids_page").strip() or "bids_page"

    registered_item_id = request.form.get("registered_item_id", "").strip()
    registered_bidder_id = request.form.get("registered_bidder_id", "").strip()
    if not registered_item_id or not registered_bidder_id:
        return redirect(url_for(redirect_target, message="Choose an available item and a registered bidder."))

    reg_item = next((i for i in data["items"] if i["item_id"] == registered_item_id), None)
    if not reg_item or reg_item.get("status", "Available") != "Available":
        return redirect(url_for(redirect_target, message="That item is not available for bidding."))

    reg_bidder = next((b for b in data["bidders"] if b["bidders_id"] == registered_bidder_id), None)
    if not reg_bidder or int(reg_bidder.get("participation_fee_paid", 0) or 0) < PARTICIPATION_FEE:
        return redirect(url_for(redirect_target, message="Register the bidder and confirm the participation fee before bidding."))
    if reg_bidder.get("auction_id") != reg_item.get("auction_id"):
        return redirect(url_for(redirect_target, message="Select a bidder registered for this item's auction."))

    try:
        amount = int(request.form["amount"])
    except (KeyError, ValueError):
        return redirect(url_for(redirect_target, message="Enter a valid whole-number bid amount."))
    if amount < int(reg_item["starting_price"]):
        return redirect(url_for(redirect_target, message="Your bid must be at least the item's starting price."))

    item_id = reg_item["item_id"]
    item_name = reg_item["item_name"]
    category = reg_item["category"]
    condition = reg_item["condition"]
    starting_price = int(reg_item["starting_price"])
    reserved_price = int(reg_item["reserved_price"])
    seller_id = reg_item["seller_id"]
    auction_id = reg_item["auction_id"]

    if not auction_is_open(data, auction_id):
        return redirect(url_for(redirect_target, message="Start the auction before placing bids."))

    bidder_name = reg_bidder["name"]
    contact = reg_bidder["contact"]
    address = reg_bidder["address"]
    gender = reg_bidder["gender"]
    birth_year = reg_bidder["birth_year"]
    assigned_bidder_id = reg_bidder["bidders_id"]

    matched_auc_dict = next((a for a in data["auctions"] if a["auction_id"] == auction_id), None)
    matched_auc = make_auction(matched_auc_dict)
    matched_sel_dict = next((s for s in data["sellers"] if s["seller_id"] == seller_id), {})
    matched_sel = make_seller(matched_sel_dict, matched_auc_dict)

    created_item = make_item({
        "item_id": item_id,
        "item_name": item_name,
        "category": category,
        "condition": condition,
        "starting_price": starting_price,
        "reserved_price": reserved_price,
        "status": "Available",
    }, matched_sel_dict, matched_auc_dict)
    created_bidder = make_bidder({
        "name": bidder_name,
        "contact": contact,
        "address": address,
        "bidders_id": assigned_bidder_id,
        "gender": gender,
        "birth_year": birth_year,
    }, matched_auc_dict)
    timestamp = datetime.now()
    bid = make_bid({
        "amount": amount,
        "date": timestamp.strftime("%d-%m-%Y"),
        "time": timestamp.strftime("%H:%M:%S"),
    }, {
        "name": created_bidder.name,
        "contact": created_bidder.contact,
        "address": created_bidder.address,
        "bidders_id": created_bidder.bidders_id,
        "gender": created_bidder.gender,
        "birth_year": created_bidder.birth_year,
    }, {
        "item_id": created_item.item_id,
        "item_name": created_item.item_name,
        "category": created_item.category,
        "condition": created_item.condition,
        "starting_price": created_item.starting_price,
        "reserved_price": reserved_price,
        "status": created_item.status,
    }, matched_sel_dict, matched_auc_dict)
    created_bidder.register()
    bid.show_bid_details()

    meets_reserve = created_item.verify_reserve_price(amount)

    data["bids"].append({
        "bid_id": next_auto_id("BID", [b.get("bid_id", "") for b in data["bids"]], digits=3),
        "amount": bid.amount,
        "item_id": created_item.item_id,
        "item_name": created_item.item_name,
        "category": created_item.category,
        "condition": created_item.condition,
        "starting_price": created_item.starting_price,
        "reserved_price": reserved_price,
        "meets_reserve": meets_reserve,
        "status": created_item.status,
        "seller_id": seller_id,
        "auction_id": auction_id,
        "bidders_id": created_bidder.bidders_id,
        "bidder_name": created_bidder.name,
        "contact": created_bidder.contact,
        "address": created_bidder.address,
        "gender": created_bidder.gender,
        "birth_year": created_bidder.birth_year,
        "date": bid.date,
        "time": bid.time,
        "bid_status": "Active",
    })
    save_data(data)
    return redirect(url_for(redirect_target))


@auction_manager.route("/withdraw_bid/<bid_id>", methods=["POST"])
def withdraw_bid(bid_id):
    """Keep a bid in history while removing it from all active standings."""
    data = load_data()
    bid = next((b for b in data["bids"] if b.get("bid_id") == bid_id), None)
    latest_active_bid = next(
        (
            candidate for candidate in reversed(data["bids"])
            if bid
            and candidate.get("bidders_id") == bid.get("bidders_id")
            and candidate.get("item_id") == bid.get("item_id")
            and candidate.get("bid_status", "Active") == "Active"
        ),
        None,
    )
    if bid and bid is latest_active_bid:
        bid["bid_status"] = "Withdrawn"
        save_data(data)
    return redirect(url_for("bids_page"))


@auction_manager.route("/items")
def items_page():
    data = load_data()
    search_query = request.args.get("search", "").strip()
    items = data["items"]
    if search_query:
        query = search_query.casefold()
        items = [
            item for item in items
            if query in item.get("item_name", "").casefold()
            or query in item.get("item_id", "").casefold()
        ]
    return render_template(
        "items.html",
        items=items,
        search_query=search_query,
    )


# --- WINNERS & PAYMENTS ROUTES ---
@auction_manager.route("/winners")
def winners_page():
    data = load_data()
    standings = []
    for auction in data["auctions"]:
        for item in data["items"]:
            if item.get("auction_id") != auction["auction_id"]:
                continue
            item_bids = [
                bid for bid in active_bids(data)
                if bid.get("auction_id") == auction["auction_id"]
                and bid.get("item_id") == item["item_id"]
            ]
            leader = max(item_bids, key=lambda bid: bid["amount"], default=None)
            standings.append({
                "auction_id": auction["auction_id"],
                "auction_name": auction["auction_name"],
                "auction_status": auction.get("status", "Open"),
                "item_id": item["item_id"],
                "item_name": item["item_name"],
                "bid_count": len(item_bids),
                "leader_name": leader["bidder_name"] if leader else "No bids yet",
                "leader_amount": leader["amount"] if leader else 0,
            })

    return render_template(
        "winners.html",
        winners=data["winners"],
        pending_winners=[
            winner for winner in data["winners"]
            if winner.get("payment_status") in {"Pending", "Pending Payment"}
        ],
        payments=data["payments"],
        bids=data["bids"],
        auctions=[
            auction for auction in data["auctions"]
            if auction.get("status", "Open") != "Closed"
        ],
        standings=standings,
        results=data["auction_results"],
        participation_fee=PARTICIPATION_FEE,
        status_message=request.args.get("message", ""),
    )


@auction_manager.route("/announce_winner", methods=["POST"])
def announce_winner():
    auction_id = request.form.get("auction_id", "").strip()
    return close_auction(auction_id)


@auction_manager.route("/add_payment", methods=["POST"])
def add_payment():
    data = load_data()
    auto_payment_id = next_auto_id("PAY", [p["payment_id"] for p in data["payments"]], digits=3)
    auto_transaction_id = f"TXN-{random.randint(100000, 999999)}"

    winner_id = request.form.get("winner_id", "").strip()
    matched_winner = next((w for w in data["winners"] if w["winner_id"] == winner_id), None)
    if matched_winner is None or matched_winner.get("payment_status") not in {"Pending", "Pending Payment"}:
        return redirect(url_for("winners_page", message="Select a winner with a pending payment."))

    item_name = matched_winner["item_name"]
    winner_name = matched_winner["name"]
    winning_bid_amount = matched_winner["final_bid"]
    amount = winning_bid_amount

    currency = request.form["currency"].strip()
    payment_method = request.form["payment_method"].strip()

    matched_bid_data = next(
        (bid for bid in data["bids"] if bid.get("item_id") == matched_winner["item_id"]),
        {},
    )
    auction_data = next(
        (auction for auction in data["auctions"] if auction["auction_id"] == matched_winner["auction_id"]),
        {},
    )
    item_data = next(
        (item for item in data["items"] if item["item_id"] == matched_winner["item_id"]),
        {"item_id": matched_winner["item_id"], "item_name": item_name, "starting_price": amount,
         "reserved_price": amount, "status": "Sold"},
    )
    seller_data = next(
        (seller for seller in data["sellers"] if seller["seller_id"] == item_data.get("seller_id")),
        {},
    )
    bidder_data = {
        "name": winner_name,
        "contact": matched_winner.get("contact", ""),
        "address": "",
        "bidders_id": matched_winner["bidders_id"],
        "gender": "",
        "birth_year": "",
    }
    payment = make_payment(
        auto_payment_id,
        matched_bid_data.get("bid_id", ""),
        auto_transaction_id,
        currency,
        payment_method,
        {"amount": amount, "date": matched_bid_data.get("date", ""), "time": matched_bid_data.get("time", "")},
        bidder_data,
        item_data,
        seller_data,
        auction_data,
    )
    payment.process_payment()

    matched_winner["payment_status"] = "Completed"
    for result in data["auction_results"]:
        if result.get("auction_id") != matched_winner["auction_id"]:
            continue
        for result_item in result.get("items", []):
            if result_item.get("item_id") == matched_winner["item_id"]:
                result_item["payment_status"] = "Completed"
    for bid in data["bids"]:
        if (
            bid.get("auction_id") == matched_winner["auction_id"]
            and bid.get("item_id") == matched_winner["item_id"]
            and bid.get("bidders_id") == matched_winner["bidders_id"]
            and bid.get("bid_status") == "Winning bid"
        ):
            bid["payment_status"] = "Completed"

    data["payments"].append({
        "payment_id": payment.payment_id,
        "winner_id": winner_id,
        "winner_name": winner_name,
        "item_name": item_name,
        "winning_bid": winning_bid_amount,
        "added_fee": 0,
        "amount": amount,
        "transaction_id": payment.transaction_id,
        "currency": payment.currency,
        "payment_method": payment.payment_method,
    })
    save_data(data)
    return redirect(url_for("winners_page"))


if __name__ == "__main__":
    auction_manager.run(debug=True, port=7000)
