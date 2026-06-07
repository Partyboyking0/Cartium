SUPPORTED_INTENTS = {
    "product_search", "product_comparison", "product_details", "stock_check", "add_to_cart",
    "remove_from_cart", "view_cart", "order_status", "return_policy", "shipping_policy",
    "refund_policy", "payment_help", "personalized_recommendation", "general_help",
}


def classify_intent(message: str) -> str:
    text = (message or "").lower()
    if any(phrase in text for phrase in ["add to cart", "add ctm", "add product"]):
        return "add_to_cart"
    if "remove from cart" in text or "delete from cart" in text:
        return "remove_from_cart"
    if "show my cart" in text or "view cart" in text or "my cart" in text:
        return "view_cart"
    if any(phrase in text for phrase in ["compare", "difference between", "versus", " vs "]):
        return "product_comparison"
    if any(word in text for word in ["available", "stock", "size"]):
        return "stock_check"
    if any(phrase in text for phrase in ["where is my order", "track", "order status"]):
        return "order_status"
    if "order" in text and any(word in text for word in ["status", "track", "placed", "shipped", "delivered"]):
        return "order_status"
    if "return policy" in text or text.strip() == "returns" or "return" in text:
        return "return_policy"
    if "shipping" in text or "delivery" in text:
        return "shipping_policy"
    if "refund" in text:
        return "refund_policy"
    if any(word in text for word in ["payment", "payments", "pay", "razorpay", "upi", "card", "wallet", "netbanking"]):
        return "payment_help"
    if any(phrase in text for phrase in ["based on my history", "for me", "my preference", "personalized"]):
        return "personalized_recommendation"
    if any(word in text for word in ["suggest", "show", "find", "recommend", "under", "below", "gift", "hoodie", "sneaker"]):
        return "product_search"
    if any(word in text for word in ["details", "spec", "features", "about"]):
        return "product_details"
    return "general_help"
