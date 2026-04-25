// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title UncheckedCall1 - Low-level .call() return value ignored
/// @notice If recipient is a contract and reverts, caller doesn't know — funds lost
contract UncheckedCall1 {
    address public owner;

    constructor() public {
        owner = msg.sender;
    }

    modifier onlyOwner() {
        require(msg.sender == owner);
        _;
    }

    /// @notice BAD: .call() return value not checked
    function sendEth(address recipient, uint256 amount) public onlyOwner {
        recipient.call.value(amount)(""); // return value ignored — silent failure
    }

    /// @notice BAD: .send() returns bool but result is unused
    function sendWithSend(address recipient) public onlyOwner {
        recipient.send(1 ether); // false return silently ignored
    }

    function deposit() public payable {}
}
