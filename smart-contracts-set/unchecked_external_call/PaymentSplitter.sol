// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title PaymentSplitter - Unchecked calls in loop (DoS + silent failure)
/// @notice If any recipient rejects ETH, remaining recipients get nothing silently
contract PaymentSplitter {
    address public owner;
    address[] public payees;

    event PaymentSent(address indexed to, uint256 amount);

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }

    function addPayee(address payee) public onlyOwner {
        payees.push(payee);
    }

    /// @notice BAD: unchecked .call inside loop — one failure silently skips others
    function distributePayments() public payable onlyOwner {
        uint256 share = msg.value / payees.length;
        for (uint256 i = 0; i < payees.length; i++) {
            // BAD: return value of .call not checked, silent failure
            payees[i].call.value(share)("");
            emit PaymentSent(payees[i], share);
        }
    }

    /// @notice Also bad: .send in a loop returns bool but result ignored
    function distributeWithSend() public payable onlyOwner {
        uint256 share = msg.value / payees.length;
        for (uint256 i = 0; i < payees.length; i++) {
            payees[i].send(share); // unchecked bool return
        }
    }

    function balance() public view returns (uint256) {
        return address(this).balance;
    }
}
