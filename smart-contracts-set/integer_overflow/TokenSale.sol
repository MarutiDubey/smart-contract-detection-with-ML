// SPDX-License-Identifier: MIT
pragma solidity ^0.4.24;

/// @title IntegerOverflow2 - Unsigned integer underflow via subtraction
/// @notice Classic underflow: subtracting more than balance wraps to max uint
contract TokenSale {
    mapping(address => uint256) public balances;
    uint256 public totalSupply;
    uint256 public constant PRICE = 1 ether;

    constructor() public {
        totalSupply = 1000000;
        balances[msg.sender] = totalSupply;
    }

    function buy(uint256 amount) public payable {
        // BAD: no SafeMath, Solidity <0.8 doesn't auto-revert on overflow
        require(msg.value == amount * PRICE);
        balances[msg.sender] += amount; // overflow possible if amount is huge
    }

    function sell(uint256 amount) public {
        // BAD UNDERFLOW: if amount > balances[msg.sender], wraps to huge number
        balances[msg.sender] -= amount;
        totalSupply -= amount;
        msg.sender.transfer(amount * PRICE);
    }
}
