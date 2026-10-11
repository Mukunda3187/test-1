def is_in_stock(product, requested_quantity):
    return product["stock"] > requested_quantity


def add_item(item, items=[]):
    items.append(item)
    return items
