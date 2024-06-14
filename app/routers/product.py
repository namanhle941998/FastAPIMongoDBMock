from fastapi import APIRouter, HTTPException, Depends
from middleware import crud, models, schemas, dependencies, authorization
from utilites import constants

router = APIRouter()

# Endpoints for users
@router.get("/get_all_items", response_model=list[models.Item])
def get_all_items(page: int, num_per_page: int, sort_by_column: str, is_ascend: bool, current_user=Depends(dependencies.get_current_user)):
    authorization.require_one_of_roles([constants.Role.USER, constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    # all_items = crud.get_all_items()
    all_items = crud.get_items_by_page(page, num_per_page, sort_by_column, is_ascend)
    return all_items


@router.get("/get_all_items_by_name", response_model=list[models.Item])
def get_items_by_name(
    substring: str, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.USER, constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    filtered_items = crud.get_items_by_name(substring)
    return filtered_items


@router.get("/get_all_items_by_price_range", response_model=list[models.Item])
def get_item_by_price_range(
    lower_bound: int = 0,
    upper_bound: int = 100000000,
    current_user=Depends(dependencies.get_current_user),
):
    authorization.require_one_of_roles([constants.Role.USER, constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    filtered_items = crud.get_items_by_price_range(lower_bound, upper_bound)
    return filtered_items


@router.get("/get_items_quantity", response_model=list[schemas.ProductQuantityResponse])
def get_items_quantity(
    item_name: str, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.USER, constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    items = crud.get_items_by_name(item_name)
    result = []
    for item in items:
        result.append({"name": item["name"], "quantity": item["quantity"]})
    return result


@router.post("/buy_items", response_model=schemas.InvoiceResponse)
def buy_items(
    info: schemas.UserCreateInvoice, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.USER, constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    print(info)
    user = crud.get_user_by_email(info.user_email)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    for item in info.items:
        item_in_db = crud.get_unique_item_by_name(item.name)
        if item_in_db is None:
            raise HTTPException(status_code=404, detail="Item not found")
        if item_in_db["quantity"] < item.quantity:
            raise HTTPException(status_code=400, detail="Not enough items in stock")

    total_amount = 0
    for item in info.items:
        total_amount += item.total
    if total_amount != info.total_amount:
        raise HTTPException(status_code=400, detail="Total amount does not match")

    for item in info.items:
        crud.update_item_quantity(item.name, -item.quantity)
    invoice = crud.create_invoice(info)
    return invoice


# Endpoints for admin
@router.post("/create_item", response_model=models.Item)
def create_item(
    info: schemas.ItemCreate, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    item = crud.create_item(info)
    return item


@router.post("/set_item_quantity")
def set_item_quantity(
    name: str, quantity: int, current_user=Depends(dependencies.get_current_user)
):
    authorization.require_one_of_roles([constants.Role.ADMIN, constants.Role.MODERATOR], current_user.email)
    crud.set_item_quantity(name, quantity)
    return {"message": "Item quantity updated successfully"}
