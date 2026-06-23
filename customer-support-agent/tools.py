from agents import RunContextWrapper, function_tool

from models import OrderItem, RestaurantContext


@function_tool
def add_to_order(
    wrapper: RunContextWrapper[RestaurantContext], item_name: str, quantity: int
):
    """메뉴 항목과 수량을 현재 고객의 장바구니에 추가한다.

    사용자가 명확한 메뉴와 수량으로 주문을 확정했을 때 호출한다.

    Args:
        item_name: 장바구니에 추가할 메뉴 이름.
        quantity: 장바구니에 추가할 수량.
    """
    wrapper.context.order.append(OrderItem(name=item_name, quantity=quantity))
    return f"🛒 {item_name} {quantity}개를 장바구니에 담았습니다."


@function_tool
def confirm_order(wrapper: RunContextWrapper[RestaurantContext]):
    """현재 장바구니에 저장된 모든 주문 항목과 수량을 조회한다.

    사용자가 장바구니, 주문 내역 또는 담긴 메뉴를 확인해 달라고 요청하면
    반드시 호출한다.
    """
    if not wrapper.context.order:
        return "장바구니가 비어있습니다."

    summary = "\n".join(
        f"📌 {item.name} x {item.quantity}" for item in wrapper.context.order
    )
    return f"현재 주문 내역:\n{summary}"


@function_tool
def confirm_reservation(party_size: int, reservation_date: str, reservation_time: str):
    """사용자가 예약 내용을 승인하면 예약을 확정한다."""
    return (
        "예약이 확정되었습니다. \n"
        f"- 인원수: {party_size}명\n"
        f"- 날짜: {reservation_date}\n"
        f"- 시간: {reservation_time}"
    )
