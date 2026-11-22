import time


class Auction:
    def __init__(self, auction_id, date, start_time, end_time, location, auction_name):
        self.auction_id = auction_id
        self.date = date
        self.start_time = start_time
        self.end_time = end_time
        self.location = location
        self.auction_name = auction_name

    def start_auction(self):
        print(f"Auction '{self.auction_name}' has started at {self.location}!")

    def end_auction(self):
        print(f"Auction '{self.auction_name}' has ended.")

    def find_highest_bid(self, bids_list):
        if not bids_list:
            return None

        highest_bid = bids_list[0]
        for bid in bids_list:
            if bid.amount > highest_bid.amount:
                highest_bid = bid

        return highest_bid

    def announce_winner(self, winning_bid):
        if winning_bid:
            print(
                f"Winner: {winning_bid.bidder.name} wins "
                f"{winning_bid.auction_item.item_name} with a bid of "
                f"${winning_bid.amount} at {self.auction_name}!"
            )
        else:
            print("No bids were placed. No winner announced.")


class Seller:
    def __init__(
        self,
        seller_id,
        name,
        company,
        contact,
        email_address,
        seller_status,
        auction_id,
        date,
        start_time,
        end_time,
        location,
        auction_name,
    ):

        self.seller_id = seller_id
        self.name = name
        self.company = company
        self.contact = contact
        self.email_address = email_address
        self.seller_status = seller_status

        # Composed object (auction_name, date, location, etc. come from here)
        self.auction = Auction(
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def start_auction(self):
        self.auction.start_auction()

    def generate_seller_id(self, existing_sellers):
        highest_number = 0

        for seller in existing_sellers:
            seller_id = seller.seller_id
            if seller_id.startswith("SEL-") and seller_id[4:].isdigit():
                number = int(seller_id[4:])
                if number > highest_number:
                    highest_number = number

        self.seller_id = f"SEL-{highest_number + 1:04}"
        return self.seller_id

    def reserve_price(self, item, price):
        self.auction.start_auction()
        print(
            f"Reserve price set to ${price} for item {item.item_name} "
            f"in {self.auction.auction_name}."
        )

    def change_reserved_price(self, item, new_price):
        print(
            f"Reserved price updated to ${new_price} for item {item.item_name} "
            f"at {self.auction.location}."
        )

    def set_description_of_item(self, item, description):
        print(f"Description set for {item.item_name}: {description}")

    def set_starting_price(self, item, price):
        item.starting_price = price
        print(
            f"Starting price for {item.item_name} set to ${price} "
            f"for {self.auction.auction_name}."
        )


class AuctionItem:
    def __init__(
        self,
        item_id,
        item_name,
        category,
        condition,
        starting_price,
        reserved_price,
        status,
        seller_id,
        seller_name,
        company,
        contact,
        email_address,
        seller_status,
        auction_id,
        date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
        self.item_id = item_id
        self.item_name = item_name
        self.category = category
        self.condition = condition
        self.starting_price = starting_price
        self.__reserved_price = reserved_price
        self.status = status

        # Composed objects (seller details and auction details come from here)
        self.seller = Seller(
            seller_id,
            seller_name,
            company,
            contact,
            email_address,
            seller_status,
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )
        self.auction = Auction(
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def update_item_status(self, new_status):
        self.status = new_status
        self.seller.set_description_of_item(
            self, f"Status updated to {self.status}"
        )
        print(f"Item '{self.item_name}' status updated to: {self.status}")

    def verify_reserve_price(self, bid_amount):
        self.seller.reserve_price(self, self.__reserved_price)
        return bid_amount >= self.__reserved_price

    def meets_starting_price(self, bid_amount):
        self.seller.set_starting_price(self, self.starting_price)
        return bid_amount >= self.starting_price


class ItemSpecification:
    def __init__(
        self,
        item_id,
        item_name,
        category,
        condition,
        base_price,
        reserved_price,
        status,
        seller_id,
        seller_name,
        company,
        contact,
        email_address,
        seller_status,
        auction_id,
        date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
       
        self.item_id = item_id
        self.category = category
        self.condition = condition
        self.base_price = base_price
        self.reserved_price = reserved_price
        self.status = status

        # Composed objects (item_name and auction_name come from here)
        self.auction_item = AuctionItem(
            item_id,
            item_name,
            category,
            condition,
            base_price,
            reserved_price,
            status,
            seller_id,
            seller_name,
            company,
            contact,
            email_address,
            seller_status,
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )
        self.auction = Auction(
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def meets_starting_price(self, bid_amount):
        return self.auction_item.meets_starting_price(bid_amount)

    def verify_reserve_price(self, bid_amount):
        return self.auction_item.verify_reserve_price(bid_amount)

    def update_item_status(self, new_status):
        self.status = new_status
        self.auction_item.update_item_status(new_status)

    def display_specification(self):
        self.auction_item.update_item_status(self.status)
        print(f"Auction: {self.auction.auction_name}")
        print(f"Item ID: {self.item_id}")
        print(f"Item: {self.auction_item.item_name}")
        print(f"Category: {self.category}")
        print(f"Condition: {self.condition}")
        print(f"Base Price: {self.base_price}")
        print(f"Reserved Price: {self.reserved_price}")
        print(f"Status: {self.status}")
        print(
            f"Validates Base Price: "
            f"{self.auction_item.meets_starting_price(self.base_price)}"
        )


class Bidder:
    def __init__(
        self,
        name,
        contact,
        address,
        bidders_id,
        gender,
        birth_year,
        auction_id,
        date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
       
        self.name = name
        self.contact = contact
        self.address = address
        self.bidders_id = bidders_id
        self.gender = gender
        self.birth_year = birth_year
        self.auction = auction

        # Composed object (auction_name, date, location, etc. come from here)
        auction = Auction(
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def generate_bidder_id(self, existing_bidders):
        highest_number = 0

        for bidder in existing_bidders:
            if bidder.bidders_id:
                number = int(bidder.bidders_id[1:])
                if number > highest_number:
                    highest_number = number

        self.bidders_id = f"B{highest_number + 1:03}"
        return self.bidders_id

    def __str__(self):
        return (
            f"Name: {self.name}\n"
            f"Contact: {self.contact}\n"
            f"Address: {self.address}\n"
            f"ID: {self.bidders_id}\n"
            f"Gender: {self.gender}\n"
            f"Birth year: {self.birth_year}"
        )

    def make_payment(self, amount=None):
        if amount is None:
            self.auction.end_auction()
        print(f"{self.name}")

    def place_bid(self, item, amount):
        print(f"{self.name} placed a bid of ${amount} on {item.item_name}.")

    def withdraw_bid(self, item):
        print(f"{self.name} withdrew their bid on {item.item_name}.")

    def register(self):
        self.auction.start_auction()
        print(f"Bidder {self.name} is successfully registered.")


class Bid:
    def __init__(
        self,
        bid_amount,
        bid_date,
        bid_time,
        bidder_name,
        bidder_contact,
        address,
        bidders_id,
        gender,
        birth_year,
        item_id,
        item_name,
        category,
        condition,
        starting_price,
        reserved_price,
        status,
        seller_id,
        seller_name,
        company,
        seller_contact,
        email_address,
        seller_status,
        auction_id,
        auction_date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
       
        self.amount = bid_amount
        self.date = bid_date
        self.time = bid_time

        # Composed objects (bidder_name, item_name, and auction_name come from here)
        self.bidder = Bidder(
            bidder_name,
            bidder_contact,
            address,
            bidders_id,
            gender,
            birth_year,
            auction_id,
            auction_date,
            start_time,
            end_time,
            location,
            auction_name,
        )
        self.auction_item = AuctionItem(
            item_id,
            item_name,
            category,
            condition,
            starting_price,
            reserved_price,
            status,
            seller_id,
            seller_name,
            company,
            seller_contact,
            email_address,
            seller_status,
            auction_id,
            auction_date,
            start_time,
            end_time,
            location,
            auction_name,
        )
        self.auction = Auction(
            auction_id,
            auction_date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def place_bid(self):
        if self.validate_amount():
            self.bidder.register()
            self.bidder.place_bid(self.auction_item, self.amount)
            self.auction_item.update_item_status("Active Bid")
            print(
                f"Valid bid of ${self.amount} placed by {self.bidder.name} "
                f"on {self.auction_item.item_name} in {self.auction.auction_name}."
            )
        else:
            print("Bid amount is lower than the item's starting price!")

    def validate_amount(self):
        return self.auction_item.meets_starting_price(self.amount)

    def show_bid_details(self):
        print(
            f"Bid of ${self.amount} by {self.bidder.name} "
            f"on {self.auction_item.item_name} ({self.auction.auction_name})."
        )

    def update_status(self):
        self.auction_item.update_item_status("Updated")
        print("Bid status updated successfully.")

    def show_highest_bidder(self, highest_bidder_name, highest_amount):
        print(f"Current Highest Bidder: {highest_bidder_name} with ${highest_amount}")

    def check_if_activity(self):
        return True


class SuccessfulWinner(Bidder):
    def __init__(
        self,
        winner_id,
        bidder_id,
        bidder_name,
        winning_item_id,
        winning_item_name,
        category,
        condition,
        starting_price,
        reserved_price,
        status,
        final_bid,
        contact,
        address,
        gender,
        birth_year,
        seller_id,
        seller_name,
        company,
        seller_contact,
        email_address,
        seller_status,
        auction_id,
        date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
        super().__init__(
            bidder_name,
            contact,
            address,
            bidder_id,
            gender,
            birth_year,
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )
       
        self.winner_id = winner_id
        self.winning_item_id = winning_item_id
        self.final_bid = final_bid

        # Composed object (winning_item_name comes from self.auction_item.item_name)
        self.auction_item = AuctionItem(
            winning_item_id,
            winning_item_name,
            category,
            condition,
            starting_price,
            reserved_price,
            status,
            seller_id,
            seller_name,
            company,
            seller_contact,
            email_address,
            seller_status,
            auction_id,
            date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def make_payment(self):
        print(
            f"{self.name} is making a payment of ${self.final_bid} "
            f"for {self.auction_item.item_name}."
        )

    def display_winner_details(self):
        print("\n--- Winner Summary ---")
        print(f"Auction: {self.auction.auction_name}")
        print(f"Winner ID: {self.winner_id}")
        print(f"Name: {self.name}")
        print(f"Won Item ID: {self.winning_item_id}")
        print(f"Won Item: {self.auction_item.item_name}")
        print(f"Final Winning Bid: ${self.final_bid}")


class Payment:
    def __init__(
        self,
        payment_id,
        bid_id,
        transaction_id,
        currency,
        payment_method,
        bid_amount,
        bid_date,
        bid_time,
        bidder_name,
        bidder_contact,
        address,
        bidders_id,
        gender,
        birth_year,
        item_id,
        item_name,
        category,
        condition,
        starting_price,
        reserved_price,
        status,
        seller_id,
        seller_name,
        company,
        seller_contact,
        email_address,
        seller_status,
        auction_id,
        auction_date,
        start_time,
        end_time,
        location,
        auction_name,
    ):
        
        self.payment_id = payment_id
        self.bid_id = bid_id
        self.transaction_id = transaction_id
        self.currency = currency
        self.payment_method = payment_method

        # Composed object (bid amount, bidder, and item come from self.bid)
        self.bid = Bid(
            bid_amount,
            bid_date,
            bid_time,
            bidder_name,
            bidder_contact,
            address,
            bidders_id,
            gender,
            birth_year,
            item_id,
            item_name,
            category,
            condition,
            starting_price,
            reserved_price,
            status,
            seller_id,
            seller_name,
            company,
            seller_contact,
            email_address,
            seller_status,
            auction_id,
            auction_date,
            start_time,
            end_time,
            location,
            auction_name,
        )

    def process_payment(self):
        print(
            f"Processing payment of {self.bid.amount} {self.currency} "
            f"by {self.bid.bidder.name} for {self.bid.auction_item.item_name} "
            f"via {self.payment_method} (Transaction ID: {self.transaction_id})..."
        )
        time.sleep(2)
        print("Payment Successful!")

    def refund(self):
        print(f"Refund of {self.bid.amount} {self.currency} processed successfully.")