// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

/// @title Escrow - A safe 3-party escrow contract
/// @notice Trusted arbitration, no reentrancy risk, explicit state machine
contract Escrow {
    enum State { AWAITING_PAYMENT, AWAITING_DELIVERY, COMPLETE, REFUNDED }

    address public buyer;
    address public seller;
    address public arbitrator;
    uint256 public amount;
    State public state;

    event PaymentDeposited(address indexed buyer, uint256 amount);
    event DeliveryConfirmed(address indexed buyer);
    event RefundIssued(address indexed buyer, uint256 amount);

    modifier onlyBuyer() { require(msg.sender == buyer, "Only buyer"); _; }
    modifier onlyArbitrator() { require(msg.sender == arbitrator, "Only arbitrator"); _; }
    modifier inState(State expected) { require(state == expected, "Wrong state"); _; }

    constructor(address _seller, address _arbitrator) {
        require(_seller != address(0) && _arbitrator != address(0), "Zero address");
        buyer = msg.sender;
        seller = _seller;
        arbitrator = _arbitrator;
        state = State.AWAITING_PAYMENT;
    }

    function deposit() external payable onlyBuyer inState(State.AWAITING_PAYMENT) {
        require(msg.value > 0, "Send ETH");
        amount = msg.value;
        state = State.AWAITING_DELIVERY;
        emit PaymentDeposited(msg.sender, msg.value);
    }

    function confirmDelivery() external onlyBuyer inState(State.AWAITING_DELIVERY) {
        state = State.COMPLETE;
        emit DeliveryConfirmed(msg.sender);
        (bool ok, ) = payable(seller).call{value: amount}("");
        require(ok, "Transfer failed");
    }

    function refundBuyer() external onlyArbitrator inState(State.AWAITING_DELIVERY) {
        state = State.REFUNDED;
        uint256 refund = amount;
        amount = 0;
        emit RefundIssued(buyer, refund);
        (bool ok, ) = payable(buyer).call{value: refund}("");
        require(ok, "Refund failed");
    }

    function getState() external view returns (State) {
        return state;
    }
}
